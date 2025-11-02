import os
import json
import shutil

def validate_categories(categories):
    # categories.json 형식 확인
    for category in categories:
        if not isinstance(category, dict):
            print("Invalid category structure: Not a dictionary.")
            return False
        required_keys = ["name", "name_kor", "preview1", "preview2", "preview3"]
        if not all(key in category for key in required_keys):
            print(f"Missing required keys in categories: {category}")
            return False
    return True

def validate_wallpapers(wallpapers):
    # wallpapers.json 형식 확인
    for wallpaper in wallpapers:
        if not isinstance(wallpaper, dict):
            print("Invalid wallpaper structure: Not a dictionary.")
            return False
        required_keys = ["name", "url", "categories", "premium"]
        # 필요한 필드들이 모두 있는지 확인
        if not all(key in wallpaper for key in required_keys):
            print(f"Missing required keys in wallpaper: {wallpaper}")
            return False
        # premium 필드가 boolean 값인지 확인
        if not isinstance(wallpaper["premium"], bool):
            print(f"Invalid 'premium' field in wallpaper: {wallpaper}")
            return False
        # url이 올바른 형식의 문자열인지 확인 (간단히 url이 문자열인지 체크)
        if not isinstance(wallpaper["url"], str):
            print(f"Invalid 'url' field in wallpaper: {wallpaper}")
            return False
        # categories가 문자열인지 확인
        if not isinstance(wallpaper["categories"], str):
            print(f"Invalid 'categories' field in wallpaper: {wallpaper}")
            return False
    return True

def process_folder(folder_path, error_folder, root_folder):
    print(f"검사 중: {folder_path}")
    # categories.json과 wallpapers.json 검사
    categories_file = os.path.join(folder_path, 'categories.json')
    wallpapers_file = os.path.join(folder_path, 'wallpapers.json')

    folder_has_error = False  # 폴더에 오류가 있는지 체크할 변수

    if os.path.isfile(categories_file):
        try:
            with open(categories_file, 'r', encoding='utf-8') as file:
                categories = json.load(file)
            if not validate_categories(categories):
                print(f"잘못된 categories.json 발견: {categories_file}")
                copy_to_error_folder(categories_file, error_folder, folder_path, root_folder)
                folder_has_error = True
        except json.JSONDecodeError:
            print(f"categories.json 파일 구문 오류: {categories_file}")
            copy_to_error_folder(categories_file, error_folder, folder_path, root_folder)
            folder_has_error = True

    if os.path.isfile(wallpapers_file):
        try:
            with open(wallpapers_file, 'r', encoding='utf-8') as file:
                wallpapers = json.load(file)
            if not validate_wallpapers(wallpapers):
                print(f"잘못된 wallpapers.json 발견: {wallpapers_file}")
                copy_to_error_folder(wallpapers_file, error_folder, folder_path, root_folder)
                folder_has_error = True
        except json.JSONDecodeError:
            print(f"wallpapers.json 파일 구문 오류: {wallpapers_file}")
            copy_to_error_folder(wallpapers_file, error_folder, folder_path, root_folder)
            folder_has_error = True

    # 하위 폴더 탐색
    for root, dirs, files in os.walk(folder_path):
        for sub_dir in dirs:
            process_folder(os.path.join(root, sub_dir), error_folder, root_folder)

    # 오류가 있는 폴더는 @@error 폴더로 복사
    if folder_has_error:
        copy_folder_to_error(folder_path, error_folder, root_folder)

def copy_to_error_folder(file_path, error_folder, folder_path, root_folder):
    # error 폴더가 없으면 생성
    if not os.path.exists(error_folder):
        print(f"@@error 폴더가 없습니다. 생성 중: {error_folder}")
        os.makedirs(error_folder)
    
    # 오류 파일이 속한 폴더만 복사하므로, root_folder를 기준으로 상대 경로 계산
    relative_path = os.path.relpath(folder_path, root_folder)  # 루트 폴더 기준으로 상대 경로 구하기
    
    # error 폴더 내에 해당 폴더가 없으면 생성
    error_folder_path = os.path.join(error_folder, relative_path)
    if not os.path.exists(error_folder_path):
        os.makedirs(error_folder_path)

    # 파일 복사
    shutil.copy(file_path, error_folder_path)
    print(f"파일 복사 완료: {file_path} -> {error_folder_path}")

def copy_folder_to_error(folder_path, error_folder, root_folder):
    # error 폴더가 없으면 생성
    if not os.path.exists(error_folder):
        os.makedirs(error_folder)
    
    # 폴더 복사
    folder_name = os.path.basename(folder_path)
    destination = os.path.join(error_folder, os.path.relpath(folder_path, root_folder))

    # 오류가 발생한 폴더만 복사
    if not os.path.exists(destination):
        shutil.copytree(folder_path, destination)
        print(f"폴더 복사 완료: {folder_path} -> {destination}")
    else:
        print(f"폴더 이미 존재: {destination}")

def main():
    # 현재 작업 디렉토리 경로를 루트 폴더로 설정
    root_folder = os.getcwd()
    error_folder = os.path.join(root_folder, "@@error")

    print(f"현재 작업 디렉토리: {root_folder}")
    print(f"오류 파일이 복사될 폴더: {error_folder}")

    # 루트 폴더에서 검사 시작
    process_folder(root_folder, error_folder, root_folder)
    print("검사 완료!")

if __name__ == "__main__":
    main()
