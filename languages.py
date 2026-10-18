# Copyright (c) 2026 KEITER78
"""The 100 language codes supported by M2M100; OCR support is separate."""
LANGUAGES = {
    'ja':'日本語', 'en':'英語', 'zh':'中国語', 'ko':'韓国語',
    'fr':'フランス語', 'de':'ドイツ語', 'es':'スペイン語', 'pt':'ポルトガル語',
    'it':'イタリア語', 'ru':'ロシア語', 'ar':'アラビア語', 'hi':'ヒンディー語',
    'vi':'ベトナム語', 'th':'タイ語', 'id':'インドネシア語', 'ms':'マレー語',
    'tl':'タガログ語', 'tr':'トルコ語', 'uk':'ウクライナ語', 'pl':'ポーランド語',
    'nl':'オランダ語', 'cs':'チェコ語', 'ro':'ルーマニア語', 'hu':'ハンガリー語',
    'el':'ギリシャ語', 'sv':'スウェーデン語', 'fi':'フィンランド語',
    'da':'デンマーク語', 'no':'ノルウェー語', 'he':'ヘブライ語', 'fa':'ペルシャ語',
    'bn':'ベンガル語', 'ta':'タミル語',
    'af':'アフリカーンス語', 'am':'アムハラ語', 'ast':'アストゥリアス語',
    'az':'アゼルバイジャン語', 'ba':'バシキール語', 'be':'ベラルーシ語',
    'bg':'ブルガリア語', 'br':'ブルトン語', 'bs':'ボスニア語', 'ca':'カタルーニャ語',
    'ceb':'セブアノ語', 'cy':'ウェールズ語', 'et':'エストニア語', 'ff':'フラニ語',
    'fy':'西フリジア語', 'ga':'アイルランド語', 'gd':'スコットランド・ゲール語',
    'gl':'ガリシア語', 'gu':'グジャラート語', 'ha':'ハウサ語', 'hr':'クロアチア語',
    'ht':'ハイチ・クレオール語', 'hy':'アルメニア語', 'ig':'イボ語', 'ilo':'イロカノ語',
    'is':'アイスランド語', 'jv':'ジャワ語', 'ka':'ジョージア語', 'kk':'カザフ語',
    'km':'クメール語', 'kn':'カンナダ語', 'lb':'ルクセンブルク語', 'lg':'ガンダ語',
    'ln':'リンガラ語', 'lo':'ラオ語', 'lt':'リトアニア語', 'lv':'ラトビア語',
    'mg':'マダガスカル語', 'mk':'マケドニア語', 'ml':'マラヤーラム語',
    'mn':'モンゴル語', 'mr':'マラーティー語', 'my':'ミャンマー語', 'ne':'ネパール語',
    'ns':'北ソト語', 'oc':'オック語', 'or':'オリヤー語', 'pa':'パンジャーブ語',
    'ps':'パシュトー語', 'sd':'シンド語', 'si':'シンハラ語', 'sk':'スロバキア語',
    'sl':'スロベニア語', 'so':'ソマリ語', 'sq':'アルバニア語', 'sr':'セルビア語',
    'ss':'スワジ語', 'su':'スンダ語', 'sw':'スワヒリ語', 'tn':'ツワナ語',
    'ur':'ウルドゥー語', 'uz':'ウズベク語', 'wo':'ウォロフ語', 'xh':'コサ語',
    'yi':'イディッシュ語', 'yo':'ヨルバ語', 'zu':'ズールー語',
}
TESSERACT_CODES = dict(zip(
    'af am ar az be bg bn br bs ca ceb cs cy da de el en es et fa fi fr ga gd gl gu '
    'he hi hr ht hu hy id is it ja jv ka kk km kn ko lb lo lt lv mk ml mn mr ms my '
    'ne nl no oc or pa pl ps pt ro ru sd si sk sl sq sr su sv sw ta th tl tr uk ur uz vi yi yo'.split(),
    'afr amh ara aze bel bul ben bre bos cat ceb ces cym dan deu ell eng spa est fas fin fra gle gla glg guj '
    'heb hin hrv hat hun hye ind isl ita jpn jav kat kaz khm kan kor ltz lao lit lav mkd mal mon mar msa mya '
    'nep nld nor oci ori pan pol pus por ron rus snd sin slk slv sqi srp sun swe swa tam tha tgl tur ukr urd uzb vie yid yor'.split()
))
TESSERACT_CODES['zh'] = 'chi_sim'
TESSERACT_CODES['tl'] = 'fil'
EASYOCR_CODES = {'zh':'ch_sim'}


def validate_pair(source, target):
    if source not in LANGUAGES or target not in LANGUAGES:
        raise ValueError('対応していない言語が選択されています。')
