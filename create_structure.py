import os

# Определяем корневую папку проекта
project_root = "school147_jobs"

# Структура проекта: ключ - путь относительно корня, значение - содержимое файла (пустая строка по умолчанию)
structure = {
    # Корневые файлы
    "app.py": "",
    "config.py": "",
    "models.py": "",
    "database.py": "",
    "requirements.txt": "",
    ".env": "",

    # Static файлы
    "static/css/style.css": "",
    "static/js/main.js": "",
    "static/img/logo.png": "",  # Примечание: это создаст пустой файл. Для реального изображения нужно будет заменить его вручную.

    # Templates файлы
    "templates/base.html": "",
    "templates/index.html": "",
    "templates/vacancies.html": "",
    "templates/vacancy_detail.html": "",
    "templates/resumes.html": "",
    "templates/resume_detail.html": "",
    "templates/about.html": "",
    "templates/publish.html": "",
    "templates/apply.html": "",
    "templates/add_resume.html": "",

    # Partials
    "templates/partials/navbar.html": "",
    "templates/partials/footer.html": "",
    "templates/partials/flash_messages.html": "",
}

def create_project_structure(root, files_dict):
    for relative_path, content in files_dict.items():
        full_path = os.path.join(root, relative_path)

        # Создаем директории, если они не существуют
        directory = os.path.dirname(full_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            print(f"Создана папка: {directory}")

        # Создаем файл, если он еще не существует
        if not os.path.exists(full_path):
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Создан файл: {full_path}")
        else:
            print(f"Файл уже существует: {full_path}")

if __name__ == "__main__":
    print(f"Начинаю создание структуры проекта в '{project_root}'...")
    create_project_structure(project_root, structure)
    print("Готово!")
