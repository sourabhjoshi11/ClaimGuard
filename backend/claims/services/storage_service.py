from django.core.files.storage import default_storage


def save_uploaded_file(file, file_name):
    saved_path = default_storage.save(file_name, file)
    return {
        "saved_path": saved_path,
        "absolute_path": default_storage.path(saved_path),
        "url": default_storage.url(saved_path),
    }
