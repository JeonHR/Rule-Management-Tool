import os
import shutil
import zipfile
import subprocess
from datetime import datetime

INSTALL_ROOT = r"./TEST_SYSTEM"
RUNTIME_ROOT = os.path.join(INSTALL_ROOT, "runtime")
PATCH_CACHE = os.path.join(INSTALL_ROOT, "patch_cache")
LOG_FILE = "./patch.log"

def clean_series(product, product_series):
    """
    runtime/<Product>/<Product_Series> 만 clean
    """
    target_path = os.path.join(RUNTIME_ROOT, product, product_series)

    if os.path.exists(target_path): #파일 있으면 삭제
        shutil.rmtree(target_path)

    os.makedirs(target_path, exist_ok=True) # 파일 없으면 생성

def extract_zip(zip_path, product, product_series):
    """
    zip 전체 내용을 runtime/<Product>/<Product_Series>/ 로 압축 해제
    """
    target_root = os.path.join(RUNTIME_ROOT, product, product_series)

    

    with zipfile.ZipFile(zip_path, "r") as z:
        for member in z.infolist():
            target_path = os.path.join(target_root, member.filename)
            print(f"Extracting {member.filename} to {target_path}")

            

            if member.is_dir():
                os.makedirs(target_path, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(target_path), exist_ok=True) # Zip 폴더의 상위 폴더 생성
                with z.open(member) as src, open(target_path, "wb") as dst: 
                    shutil.copyfileobj(src, dst)

def patch_product(product, series, program_name):
    product_series = f"{product}_{series}"
    zip_path = os.path.join(PATCH_CACHE, f"{product_series}.zip")
    
    # 0. 실행 중 프로그램 체크
    check_running_or_abort(product, series, program_name)

    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"{product_series}.zip not found")

    validate_zip_name(zip_path, product, series)
    validate_zip_basic(zip_path)
    

    # 1. Series 영역 clean
    clean_series(product, product_series)

    # 2. zip 전체 압축 해제
    extract_zip(zip_path, product, product_series)

    print(f"[OK] Patch 완료 → runtime/{product}/{product_series}")

    write_log_txt(
        action="PATCH",
        product=product,
        series=series,
        zip=os.path.basename(zip_path),
        result="SUCCESS"
    )


def validate_zip_basic(zip_path):
    if not zipfile.is_zipfile(zip_path):
        raise ValueError("Not a zip file")

    with zipfile.ZipFile(zip_path, "r") as z:
        bad = z.testzip()   # CRC 체크
        if bad:
            raise ValueError(f"Corrupted file in zip: {bad}")

        if len(z.namelist()) == 0:
            raise ValueError("Empty zip")

    print("[OK] Zip validation passed")

def validate_zip_name(zip_path, product, series):
    name = os.path.basename(zip_path) # Zip 파일 이름
    expected = f"{product}_{series}.zip"
    if name != expected:
        raise ValueError(f"Zip name mismatch: {name}")
    print("[OK] Zip name validation passed")



def is_process_running(process_name):
    result = subprocess.run(
        ["tasklist"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return process_name.lower() in result.stdout.lower()

def check_running_or_abort(product, series, program_name):
    if is_process_running(program_name):
        write_log_txt(
            action="PATCH",
            product=product,
            series=series,
            result="FAIL",
            reason="PROGRAM_RUNNING",
            process=program_name
        )
        raise RuntimeError("Patch aborted: program running")

def write_log_txt(**kwargs):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    parts = [f"{k}={v}" for k, v in kwargs.items()]
    line = f"{ts} | " + " | ".join(parts)

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


if __name__ == "__main__":
    # patch_product("Tanami", "2025")

    if is_process_running("A_Test.exe"):
        raise RuntimeError("Program is running")
