import os
import sys
import time
import yt_dlp

def get_user_input(prompt, default=None, choices=None):
    while True:
        if default and choices:
            inp = input(f"{prompt} ({'/'.join(choices)}, default={default}): ").strip()
            if not inp:
                return default
        elif default:
            inp = input(f"{prompt} (default={default}): ").strip() or default
        else:
            inp = input(f"{prompt}: ").strip()
        if choices and inp not in choices:
            print(f"選択肢は {choices} のいずれかです。再度入力してください。")
            continue
        return inp

def main():
    url = get_user_input('動画またはプレイリストのURLを入力してください')
    bitrate = get_user_input('音声ビットレートを入力してください', default='192', choices=['128', '192', '256', '320'])

    # プレイリスト情報取得
    ydl_opts_info = {'ignoreerrors': True, 'quiet': True, 'extract_flat': 'in_playlist'}
    with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except Exception as e:
            print(f"情報取得中にエラー: {e}")
            sys.exit(1)

    is_playlist = bool(info.get('entries'))
    playlist_title = info.get('title') if is_playlist else ''
    default_dir = playlist_title or 'downloads'

    output_dir = get_user_input('保存先フォルダーを入力してください', default=default_dir)
    tag_flag = get_user_input('mp3タグとジャケット画像を追加しますか？', default='y', choices=['y', 'n'])
    os.makedirs(output_dir, exist_ok=True)
    urls = [url]

    # 総数取得
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        try:
            info = ydl.extract_info(url, download=False)
        except Exception as e:
            print(f"情報取得中にエラー: {e}")
            sys.exit(1)

    total = len(info.get('entries', [])) if 'entries' in info else 1
    count = 0

    # 表示パラメータ
    BAR_WIDTH = 20
    # ファイル名表示幅
    NAME_WIDTH = 20
    last_fname = None
    start_time = None

    def progress_hook(d):
        nonlocal count, last_fname, start_time
        status = d.get('status')
        info_dict = d.get('info_dict', {})
        raw_name = os.path.splitext(
            os.path.basename(d.get('filename', info_dict.get('title', '')))
        )[0]
        # 切り捨て/パディング
        if len(raw_name) > NAME_WIDTH:
            name_display = raw_name[:NAME_WIDTH-3] + '...'
        else:
            name_display = raw_name.ljust(NAME_WIDTH)

        # ダウンロード開始時間リセット
        if status == 'downloading' and raw_name != last_fname:
            last_fname = raw_name
            start_time = time.time()

        downloaded = d.get('downloaded_bytes', 0)
        total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
        percent = (downloaded / total_bytes * 100) if total_bytes else 0
        downloaded_mb = downloaded / 1024 / 1024
        total_mb = total_bytes / 1024 / 1024 if total_bytes else 0

        # speedがNoneなら0にする
        speed = d.get('speed') or 0
        speed_str = f"{speed/1024/1024:.2f}MiB/s"
        speed_col = f"\033[32m{speed_str}\033[0m"

        # ETA計算
        eta_str = "--:--"
        if status == 'downloading' and downloaded and start_time:
            elapsed = time.time() - start_time
            rate = downloaded / elapsed if elapsed > 0 else 0
            rem = total_bytes - downloaded
            eta = rem / rate if rate else 0
            m, s = divmod(int(eta), 60)
            eta_str = f"{m:02d}:{s:02d}"

        # バー描画
        filled = int(percent/100 * BAR_WIDTH)
        bar = '[' + '#' * filled + '-' * (BAR_WIDTH - filled) + ']'

        # １行上書き
        if status == 'downloading':
            sys.stdout.write(
                f"\r\033[K"
                f"[{count+1}/{total}] "
                f"{name_display} "
                f"{bar} "
                f"{percent:5.1f}% "
                f"{downloaded_mb:5.2f}/{total_mb:5.2f}MiB "
                f"{speed_col} ETA {eta_str}"
            )
            sys.stdout.flush()

        elif status == 'finished':
            sys.stdout.write(
                f"\r\033[K"
                f"[{count+1}/{total}] "
                f"{name_display} "
                f"[{'#'*BAR_WIDTH}] "
                f"{100.0:5.1f}% "
                f"{downloaded_mb:5.2f}/{total_mb:5.2f}MiB "
                f"{speed_col} 完了\n"
            )
            sys.stdout.flush()
            count += 1

    # タグ・サムネ埋め込み設定
    album = playlist_title if is_playlist else ''
    def info_hook(d):
        if tag_flag == 'y':
            if album:
                d['album'] = album
            d['artist'] = d.get('uploader')

    # yt-dlp オプション
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'ignoreerrors': True,
        'noplaylist': False,
        'quiet': True,
        'progress_hooks': [progress_hook],
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': bitrate,
        }]
    }

    if tag_flag == 'y':
        ydl_opts.update({
            'add_metadata': True,
            'writethumbnail': True,
            'prefer_ffmpeg': True,
            'postprocessor_args': ['-id3v2_version', '3'],
            'info_hooks': [info_hook],
        })
        ydl_opts['postprocessors'].extend([
            {'key': 'EmbedThumbnail'},
            {'key': 'FFmpegMetadata'},
        ])

    # ダウンロード実行
    for u in urls:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                ydl.download([u])
            except Exception as e:
                print(f"エラー: {u} のダウンロード中に {e}")

    print("\n全てのダウンロードが完了しました。")

if __name__ == '__main__':
    main()
