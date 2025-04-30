import yt_dlp
import os

def download_playlist_as_mp3(playlist_url, output_dir="downloads"):
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',  # 128 〜 320kbps
        }],
        'ignoreerrors': True,
        'noplaylist': False,  # プレイリスト全体を処理
        'quiet': False
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print("ダウンロードの開始")
        ydl.download([playlist_url])
        print("完了")

if __name__ == "__main__":
    url = input("URLを入力してください: ").strip()
    download_playlist_as_mp3(url)
