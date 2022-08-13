import dropbox
import userpaths


def get_refresh_token():
    first = "kCnkGHvGx08AAAAAAAAAA"
    second = "YFvsxD6746PorZUDhQ1Uovdly"
    return first + second + "F25DM116EWKQitiKv9"


def get_app_key():
    first = "nbtl6om7z"
    second = "bz0m9k"
    return first + second


def get_app_secret():
    first = "u03zp1gm"
    second = "wl9qh99"
    return first + second


dbx = dropbox.Dropbox(app_key=get_app_key(), app_secret=get_app_secret(), oauth2_refresh_token=get_refresh_token())


def list_files(path):
    files_list = []

    try:
        files = dbx.files_list_folder(path).entries
        for file in files:
            if isinstance(file, dropbox.files.FileMetadata):
                files_list.append(file.name)
    except Exception as e:
        print(e)
    return files_list


def dropbox_download_file(local_file_path, dropbox_file_path):
    # about 1 sec
    path = userpaths.get_local_appdata() + '\MrPowerManager' + local_file_path

    try:
        with open(path, 'wb') as f:
            _, result = dbx.files_download(path=dropbox_file_path)
            f.write(result.content)
    except Exception as e:
        print('Error downloading file from Dropbox: ' + str(e))


if __name__ == '__main__':
    # dropbox_download_file("\\test.ok", "/database/MrPio.dat")
    pass
