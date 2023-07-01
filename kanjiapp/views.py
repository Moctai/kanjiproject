import jaconv
import re
import math
from django.shortcuts import render
from django.views.generic.base import TemplateView
from django.db.models import Q
from django.utils.datastructures import MultiValueDictKeyError
from .models import Eg, EgList, Item, ItemId, Ref, RefList, Tag

# Create your views here.

# postされた情報を一時的に格納するためのディクショナリ
posted_data = {"text": ""}


class IndexView(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)


        # ランダム表示
        rows = Item.objects.filter(classification = 'yomi', odr = 1).values('item_id').order_by('?')[:15]
        rows = list(rows)

        item_ids = [row['item_id'] for row in rows]

        q_or = Q()
        for i in range(15):
            q_or = q_or | Q(item_id = item_ids[i])

        rows = Item.objects.filter(q_or, classification = 'hyoki', odr = 1).order_by('?')
        rows = list(rows)

        context['rand'] = [{'id': row.item_id, 'hyoki': row.txt} for row in rows]

        return context


# word/<int:p> 項目
class WordView(IndexView):
    template_name = 'word.html'

    # 項目取得
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        p = self.kwargs['p']  # p: ページ番号
        key = ['yomi', 'hyoki', 'means', 'ex', 'eg']
        item = {'ref': []}
        for k in key:
            item[k] = []

        # item_id = pのレコードを取得
        get_item = Item.objects.filter(item_id = p).order_by('odr')

        for l in get_item:
            k = l.classification

            if k != 'eg' and k != 'rel' and k != 'tag':
                if l.list_id:
                    item[k].append(get_link(l.list_id, p))
                elif l.txt:
                    item[k].append(to_ruby(l.txt))


        if item['yomi'] and item['hyoki'] and item['means']:

            # 意味が2つ以上なら番号をつける
            means_id = ['①', '②', '③', '④', '⑤', '⑥', '⑦', '⑧', '⑨', '⑩']
            if len(item['means']) > 1:

                for i in range(len(item['means'])):
                    item['means'][i] = means_id[i] + ' ' + item['means'][i]


            # -----
            # 出典
            # -----
            rows = Ref.objects.select_related('ref').filter(item_id = p)

            refsList = [{
                'yomi': row.yomi,
                'hyoki': row.hyoki,
                'ref': get_ref(row.ref),
                'p_year': row.ref.p_year,
                'category': row.ref.category
                } for row in rows]

            refsListYomihyoki = []
            refsListClassified = []
            refsLength = {'yomi': 0, 'hyoki': 0}

            if refsList:
                # 出典を並べ替え
                refsList.sort(key=lambda x : x['p_year'], reverse=True)
                refsList.sort(key=lambda x : (x['yomi'], x['category']))
                refsList.sort(key=lambda x : x['hyoki'], reverse=True)

                # 読み・表記が同じものごとに仕分ける

                for l in refsList:
                    d = {'yomi': l['yomi'], 'hyoki': l['hyoki']}

                    try:
                        i = refsListYomihyoki.index(d)
                        refsListClassified[i]['ref'].append(l['ref'])

                    except ValueError:
                        refsListYomihyoki.append(d)
                        refsListClassified.append({**d, **{'ref': [l['ref']]}})

                # 出典数を数えて多い順に並べ替える
                for l in refsListClassified:
                    l['count'] = len(l['ref'])  # 出典数
                    l['yomi_len'] = len(l['yomi'])  # 読みの文字数
                    l['hyoki_len'] = len(l['hyoki'])  # 表記の文字数

                refsListClassified.sort(key=lambda x : x['count'], reverse=True)

                for i in range(len(refsListClassified)):
                    refsListClassified[i]['id'] = i  # 出典数

                # 読み・表記の文字数の最大値
                refsLength = {
                    'yomi': max(refsListClassified, key=(lambda x: x['yomi_len']))['yomi_len'],
                    'hyoki': max(refsListClassified, key=(lambda x: x['hyoki_len']))['hyoki_len']
                }


            # 用例
            item_egs = Eg.objects.select_related('list').filter(item_id = p).order_by('odr')

            for item_eg in item_egs:
                eg_ref = item_eg.list.author + '『' + item_eg.list.title + '』'
                item['eg'].append({'txt': to_ruby(item_eg.txt), 'eg': eg_ref})


            # 関連項目
            item['rel_id'] = {'rel': [], 'yomi': [], 'hyoki': []}
            item['rel'] = {'rel': [], 'yomi': [], 'hyoki': []}

            q_or = Q(item_id = p, classification = 'rel') | Q(classification = 'rel', list_id = p)

            # 同じ読みの項目
            for l in item['yomi']:
                q_or = q_or | Q(classification = 'yomi', txt = l)

            # 同じ漢字の項目
            for l in item['hyoki']:
                l_kanji = list(re.sub('[ぁ-ヿ]', '', l))
                l_re = '^[ぁ-ヿ]*' + '[ぁ-ヿ]*'.join(l_kanji) + '[ぁ-ヿ]*$'

                l_2 = l[0]
                for i in range(1, len(l)):
                    if l[i] == '々':
                        l_2 += l_2[i - 1]
                    else:
                        l_2 += l[i]

                l_kanji_2 = list(re.sub('[ぁ-ヿ]', '', l_2))
                l_re_2 = '^[ぁ-ヿ]*' + '[ぁ-ヿ]*'.join(l_kanji_2) + '[ぁ-ヿ]*$'

                q_or = q_or | Q(classification = 'hyoki', txt__regex = l_re) | Q(classification = 'hyoki', txt__regex = l_re_2)

            item_rels = Item.objects.filter(q_or)

            # 関連項目の番号を取得
            for item_rel in item_rels:
                k = item_rel.classification

                if k == 'rel' and item_rel.item_id == p:
                    i = item_rel.list_id
                else:
                    i = item_rel.item_id

                if i != p:
                    item['rel_id'][k].append(i)

            for k in item['rel_id']:
                item['rel_id'][k] = list(dict.fromkeys(item['rel_id'][k]))  # 重複をなくす
                item['rel'][k] = get_link2(1, 0, *item['rel_id'][k])


            # タグを取得
            rows = Tag.objects.select_related('tag').filter(item_id = p)
            item['tag'] = [row.tag.txt for row in rows]


            # contextに格納
            context['p'] = p
            context['tag'] = item['tag']
            context['yomi1'] = item['yomi'][0]
            context['yomi2'] = '／'.join(item['yomi'][1:])

            context['hyoki1'] = item['hyoki'][0]
            context['hyoki2'] = '／'.join(item['hyoki'][1:])

            context['means'] = item['means']
            context['ex'] = item['ex']

            context['ref'] = refsListClassified
            context['ref_len_yomi'] = (refsLength['yomi'] + 1) * 15
            context['ref_len_hyoki'] = (refsLength['hyoki'] + 1) * 15

            context['eg'] = item['eg']

            key = list(item['rel'].keys())
            context['link'] = {}
            context['link_len_yomi'] = {}
            context['link_len_hyoki'] = {}
            context['link_len_means'] = {}

            for k in key:
                if item['rel'][k]:
                    context['link'][k] = item['rel'][k][2:]
                    context['link_len_yomi'][k] = item['rel'][k][0]
                    context['link_len_hyoki'][k] = item['rel'][k][1]
                    context['link_len_means'][k] = context['link_len_yomi'][k] + context['link_len_hyoki'][k]

            context['link_header'] = {'yomi': '同じ読みの項目', 'hyoki': '同じ表記の項目'}

        else:
            self.template_name = '404.html'

        return context


# result 検索結果
class ResultView(IndexView):
    template_name = 'result.html'

    # 項目取得
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.request.GET:

            try:
                q = self.request.GET['q']  # 検索ワードを取得
                search = self.request.GET['search']  # 検索方式を取得

                try:
                    p = int(self.request.GET['p'])  # ページ番号を取得
                    if p < 1:
                        p = 1
                except (MultiValueDictKeyError, ValueError):
                    p = 1

                if q and search in ['pre', 'suf', 'par','exa', 'tag']:

                    context['q'] = q
                    context['q_txt'] = q
                    context['search'] = search
                    context['p'] = p
                    context['before_p'] = p - 1
                    context['after_p'] = p + 1

                    context['link'] = []

                    q2 = q[0]
                    for i in range(1, len(q)):
                        if q[i] == q[i - 1]:
                            q2 += '々'
                        else:
                            q2 += q[i]

                    if search == 'pre':  # 前方一致検索
                        context['search_txt'] = 'から始まる'

                        rows = Item.objects.filter(Q(classification = 'yomi') | Q(classification = 'hyoki'), Q(txt__istartswith = q) | Q(txt__istartswith = q2)).distinct()

                    elif search == 'suf':  # 後方一致検索
                        context['search_txt'] = 'で終わる'

                        rows = Item.objects.filter(Q(classification = 'yomi') | Q(classification = 'hyoki'), Q(txt__iendswith = q) | Q(txt__iendswith = q2)).distinct()

                    elif search == 'par':  # 部分一致検索
                        context['search_txt'] = 'を含む'

                        rows = Item.objects.filter(Q(classification = 'yomi') | Q(classification = 'hyoki'), Q(txt__icontains = q) | Q(txt__icontains = q2)).distinct()

                    elif search == 'exa':  # 完全一致検索
                        context['search_txt'] = 'に一致する'

                        rows = Item.objects.filter(Q(classification = 'yomi') | Q(classification = 'hyoki'), Q(txt = q) | Q(txt = q2)).distinct()

                    elif search == 'tag':  # タグ検索
                        context['q_txt'] = '#' + q
                        context['search_txt'] = 'の'

                        rows = Tag.objects.filter(tag = q).distinct()


                    if rows:
                        item_ids = [row.item_id for row in rows]
                        item_ids = list(set(item_ids))

                        context['item_count'] = len(item_ids)
                        context['page_max'] = math.ceil(len(item_ids) / 10)

                        item_ids_link = get_link2(p, 10, *item_ids)

                        context['link'] = item_ids_link[2:]
                        context['link_len_yomi'] = item_ids_link[0]
                        context['link_len_hyoki'] = item_ids_link[1]
                        context['link_len_means'] = context['link_len_yomi'] + context['link_len_hyoki']

                    return context

                else:
                    self.template_name = '404.html'
            
            except MultiValueDictKeyError:
                self.template_name = '404.html'

        else:
            self.template_name = '404.html'



# tags タグ検索
class TagsView(IndexView):
    template_name = 'tags.html'

    # 項目取得
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        try:
            q = self.request.GET['q']  # タグを取得

            # タグが一致する項目の番号を取得
            rows = Tag.objects.filter(tag = q).distinct()

            if rows:
                item_ids = [row.item_id for row in rows]
                item_ids = list(set(item_ids))

                item_ids_link = get_link2(*item_ids)

                context['link'] = item_ids_link[2:]
                context['link_len_yomi'] = item_ids_link[0]
                context['link_len_hyoki'] = item_ids_link[1]
                context['link_len_means'] = context['link_len_yomi'] + context['link_len_hyoki']

            context['q'] = q

            return context

        except MultiValueDictKeyError:
            self.template_name = 'index.html'



# source 出典一覧
class SourceView(IndexView):
    template_name = 'source.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['source'] = []

        for i in range(2):
            context['source'].append([])
            rows = RefList.objects.filter(category = i).order_by('p_year').reverse()

            for row in rows:

                context['source'][i].append(get_ref(row))


        return context


# disclaimer 免責事項
class DisclaimerView(IndexView):
    template_name = 'disclaimer.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)


        return context


# ページ番号からリンクを作成
def get_link (a, b):  # a: リンク先の番号, b: 現在の番号
    g = {}
    g['yomi'] = Item.objects.get(item_id = a, classification = 'yomi', odr = 1)
    g['hyoki'] = Item.objects.get(item_id = a, classification = 'hyoki', odr = 1)

    x = '⇨ ' + g['hyoki'].txt + '（' + g['yomi'].txt + '）'

    # 現在と同じ番号でなければリンクを作成
    if a != b:
        x = '''<a href="/word/''' + str(a) + '''">''' + x + '</a>'

    return x


# ページ番号からリンクを作成
def get_link2 (a, b, *args):  # args: リンク先の番号のlist
    x = []
    y = {'yomi': [], 'hyoki': []}

    d = {}

    if args:
        q_or = Q()
        for i in args:
            d[str(i)] = {'yomi': [], 'hyoki': [], 'means': []}
            q_or = q_or | Q(item_id = i)

        rows = Item.objects.filter(
            Q(classification = 'yomi') | Q(classification = 'hyoki') | Q(classification = 'means'),
            q_or
        ).order_by('odr')

        for row in rows:
            for i in args:
                if row.item_id == i:
                    d[str(i)][row.classification].append(row.txt)
                    break

        for i in args:
            d[str(i)]['id'] = i

            d[str(i)]['yomi1'] = d[str(i)]['yomi'][0]

            if len(d[str(i)]['yomi']) > 1:
                d[str(i)]['yomi2'] = "・".join(d[str(i)]['yomi'][1:])

            d[str(i)]['hyoki1'] = d[str(i)]['hyoki'][0]

            if len(d[str(i)]['hyoki']) > 1:
                d[str(i)]['hyoki2'] = "・".join(d[str(i)]['hyoki'][1:])

            d[str(i)]['means'] = to_ruby('／'.join(d[str(i)]['means']))


        x = [d[str(i)] for i in args]

        # 五十音順に並べ替え
        x.sort(key=lambda z: (
            ja_dict(z['yomi1']).translate(TO_NORMAL_SEION_TABLE),
            ja_dict(z['yomi1']).translate(TO_NORMAL_TABLE),
            ja_dict(z['yomi1']),
            z['yomi1']
            ))

        if b > 0:
            x = x[b * (a - 1):b * a]
        
        y['yomi'] = [len(l['yomi1']) for l in x]
        y['hyoki'] = [len(l['hyoki1']) for l in x]

        x.insert(0, min((max(y['yomi']) + 1.5) * 16, 140))
        x.insert(1, min((max(y['hyoki']) + 1.5) * 16, 140))

    return x


# 出典番号から出典文を生成
def get_ref (a):  # a: 出典番号
    try:
        x = ''
        x_cont = ''
        x_before = []
        x_after = []

        if a.contribution:
            x_cont = '「' + a.contribution + '」'

        if a.author:
            x_before.append(a.author + ' 著')
        if a.editor:
            x_before.append(a.editor + ' 編')
        if a.translator:
            x_before.append(a.translator + ' 訳')
        if a.others1:
            x_before.append(a.others1)

        if a.volume:
            x_after.append(a.volume)
        if a.edition:
            x_after.append(a.edition)
        if a.publisher:
            x_after.append(a.publisher)
        if a.p_year:
            x_after.append(a.p_year)

        x += ', '.join(x_before) + x_cont + '『' + a.title + '』' + ', '.join(x_after) + '.'
        return x

    except RefList.DoesNotExist:
        pass


# ルビ化
def to_ruby(a):  # a: 文字列
    if type(a) == str:
        x = a.replace("《", "<span class=\"ruby\">").replace("》", "</span>")
    else:
        x = ''
    
    return x


# 五十音順
DAKU_TO_SEION = {
    'ゔ': 'う',
    'が': 'が', 'ぎ': 'き', 'ぐ': 'く', 'げ': 'け', 'ご': 'こ',
    'ざ': 'さ', 'じ': 'し', 'ず': 'す', 'ぜ': 'せ', 'ぞ': 'そ',
    'だ': 'た', 'ぢ': 'ち', 'づ': 'つ', 'で': 'て', 'ど': 'と',
    'ば': 'は', 'び': 'ひ', 'ぶ': 'ふ', 'べ': 'へ', 'ぼ': 'ほ',
    'ぱ': 'は', 'ぴ': 'ひ', 'ぷ': 'ふ', 'ぺ': 'へ', 'ぽ': 'ほ',
}

SMALL_TO_NORMAL = {
    'ぁ': 'あ', 'ぃ': 'い', 'ぅ': 'う', 'ぇ': 'え', 'ぉ': 'お',
    'っ': 'つ',
    'ゃ': 'や', 'ゅ': 'ゆ', 'ょ': 'よ',
}

TO_NORMAL_SEION_TABLE = str.maketrans({**DAKU_TO_SEION, **SMALL_TO_NORMAL})
TO_NORMAL_TABLE = str.maketrans(SMALL_TO_NORMAL)

def ja_dict(a):  # a: 仮名の文字列
    x = jaconv.kata2hira(a)  # 全てひらがなに

    i = x.find('ー')

    while i >= 0:
        c = x[i - 1]

        if c in ['ぁ', 'あ', 'か', 'が', 'さ', 'ざ', 'た', 'だ', 'な', 'は', 'ば', 'ぱ', 'ま', 'ゃ', 'や', 'ら', 'わ']:
            x = x.replace('ー', 'ぁ', 1)
        elif c in ['ぃ', 'い', 'き', 'ぎ', 'し', 'じ', 'ち', 'ぢ', 'に', 'ひ', 'び', 'ぴ', 'み', 'り', 'ゐ']:
            x = x.replace('ー', 'ぃ', 1)
        elif c in ['ぅ', 'う', 'く', 'ぐ', 'す', 'ず', 'つ', 'づ', 'ぬ', 'ふ', 'ぶ', 'ぷ', 'む', 'ゅ', 'ゆ', 'る']:
            x = x.replace('ー', 'ぅ', 1)
        elif c in ['ぇ', 'え', 'け', 'げ', 'せ', 'ぜ', 'て', 'で', 'ね', 'へ', 'べ', 'ぺ', 'め', 'れ', 'ゑ']:
            x = x.replace('ー', 'ぇ', 1)
        else:
            x = x.replace('ー', 'ぉ', 1)

        i = x.find('ー')

    return x

try:
    from .views_local import *
except:
    pass