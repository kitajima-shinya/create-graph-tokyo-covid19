import pandas as pd
from flask import Flask, jsonify


app = Flask(__name__)


# https://qiita.com/nkmk/items/8b291ba019ee33429f1b
# https://stopcovid19.metro.tokyo.lg.jp/cards/monitoring-number-of-confirmed-cases/
# https://catalog.data.metro.tokyo.lg.jp/dataset/t000010d0000000068
@app.route('/display', methods=['GET'])
def get_tokyo_covid19_patients_csv():
    url = 'https://stopcovid19.metro.tokyo.lg.jp/data/130001_tokyo_covid19_patients.csv'
    df = pd.read_csv(filepath_or_buffer=url)
    # df = pd.read_csv('./130001_tokyo_covid19_patients.csv')
    # 分析対象を公表年月日，患者の年代に絞る
    df = df[['公表_年月日', '患者_年代']].copy()
    # 列名を変更しておく
    df.rename(columns={'公表_年月日': 'date_str', '患者_年代': 'age_org'},
              inplace=True)
    # date_strが文字列なので分析用にdatetime型に変換した列dateを追加しておく
    df['date'] = pd.to_datetime(df['date_str'])
    # 日時の列をカウントして公表年月日ごとの新規陽性者の総数を算出
    # ソートしないと多い順に並ぶ
    s_total = df['date'].value_counts().sort_index()
    # 陽性者数が0の日時にも値を0としてデータを追加する
    s_total_re = s_total.reindex(
        index=pd.date_range(s_total.index[0], s_total.index[-1]),
        fill_value=0
    )

    # s_total_reを後ろから指定数取り出してlistに変換
    display_size = 100
    total_list = s_total_re.tail(display_size).values.tolist()
    move_average_list = s_total_re.rolling(7).mean().tail(display_size).values.tolist()
    # reset_indexで[key, value]というtupleになるので，lambda式でtupleの先頭だけ取り出す
    date_list = list(map(lambda x: x[0], s_total_re.tail(display_size).reset_index().values.tolist()))
    max_total = max(total_list)

    y_max = max_total
    if max_total < 100:
        y_max = (max_total // 10 + 1) * 10
    elif max_total < 1000:
        y_max = (max_total // 100 + 1) * 100
    elif max_total < 10000:
        y_max = (max_total // 1000 + 1) * 1000
    #
    # pd.set_option('display.max_rows', None)
    # print(s_total_re.tail(display_size))

    # https://developers-dot-devsite-v2-prod.appspot.com/chart/image/docs/gallery/compound_charts
    # bvgは棒グラフ
    api = 'https://chart.apis.google.com/chart?cht=bvg'
    # データ列（tではなくt1にする）
    chd = '&chd=t1:' + ','.join(map(str, total_list)) + '|' + ','.join(map(str, move_average_list))
    # 出力されるグラフの画像のサイズ
    chs = '&chs=460x200'
    # <棒の幅>,<別の系列の棒との間隔>,<グループ間の間隔>
    chbh = '&chbh=3,1,1'
    # 目盛を最小値(正の値の時は0)と最大値の間で自動設定
    chds = '&chds=0,' + str(y_max)
    # 補助線：「水平間隔」「垂直間隔」「描画される線の長さ」「描画されない線の長さ」
    chg = '&chg=20,10,1,5'
    # 軸ラベルの表示
    chxt = '&chxt=y,x'
    # マーカ種,色,系列,データインデックス,サイズ
    chm = '&chm=D,0033FF,1,0,2,1'

    x_label = date_list[0].strftime('%Y/%m/%d') + '||||||||||||||||||||' \
              + date_list[20].strftime('%Y/%m/%d') + '||||||||||||||||||||' \
              + date_list[40].strftime('%Y/%m/%d') + '||||||||||||||||||||' \
              + date_list[60].strftime('%Y/%m/%d') + '||||||||||||||||||||' \
              + date_list[80].strftime('%Y/%m/%d') + '|||||||||||||||||||' \
              + date_list[99].strftime('%Y/%m/%d')

    y_label_width = int(y_max / 5)
    y_label = str(y_label_width * 1) + '|' + str(y_label_width * 2) + '|' \
              + str(y_label_width * 3) + '|' + str(y_label_width * 4) + '|' \
              + str(y_max)

    chxl = '&chxl=0:|0|' + y_label + '|1:|' + x_label
    graph = api + chs + chd + chbh + chds + chg + chxt + chm + chxl

    last_mean_seven = s_total_re.rolling(7).mean().iloc[-1]
    last_two_mean_seven = s_total_re.rolling(7).mean().iloc[-2]
    compare_mean_seven = last_mean_seven - last_two_mean_seven
    # 前日比がプラスの場合のみプラスを表示する
    plus = '+'
    if compare_mean_seven < 0:
        plus = ''

    day = df['date'].iloc[-1].strftime('%Y/%m/%d')
    new_number = s_total_re.iloc[-1]
    print(day)
    print('新規陽性者数：' + str(new_number) + '人')
    print('7日間移動平均：' + '{:.2f}'.format(last_mean_seven) + '人'
          + '（前日比：' + plus + '{:.2f}'.format(compare_mean_seven) + '人）')
    print(graph)
    result = {
        'text': day + '現在\n\n' +'新規陽性者数: ' + str(new_number) + '人\n\n' + '7日間移動平均: ' + '{:.2f}'.format(last_mean_seven)
                + '人' + '（前日比: ' + plus + '{:.2f}'.format(compare_mean_seven) + '人）\n\n' + '![](' + graph + ')' + '\n\n',
        'display': 1,
    }
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
    # get_tokyo_covid19_patients_csv()
