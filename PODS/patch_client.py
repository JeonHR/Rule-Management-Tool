import os
import shutil
import zipfile
import subprocess
from datetime import datetime
import hashlib

INSTALL_ROOT = r"./TEST_SYSTEM"
RUNTIME_ROOT = os.path.join(INSTALL_ROOT, "runtime")
PATCH_CACHE = os.path.join(INSTALL_ROOT, "patch_cache")
LOG_FILE = "./patch.log"
TMP_ROOT = os.path.join(INSTALL_ROOT, "_tmp")

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

    validate_md5(zip_path)

    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"{product_series}.zip not found")

    validate_zip_name(zip_path, product, series)
    validate_zip_basic(zip_path)
    

    # 1. Series 영역 clean
    clean_series(product, product_series)

    # 2. zip 전체 압축 해제
    extract_zip(zip_path, product, product_series)

    print(f"[OK] Patch 완료 → runtime/{product}/{product_series}")
    
    write_version_file(product, series, zip_name, md5_value)

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



def calc_md5(file_path):
    md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    return md5.hexdigest()


def read_md5_file(md5_path):
    with open(md5_path, "r", encoding="cp949") as f:
        return f.read().strip()


def validate_md5(zip_path):
    md5_path = zip_path.replace(".zip", ".md5")

    if not os.path.exists(zip_path):
        raise RuntimeError("ZIP_NOT_FOUND")

    if not os.path.exists(md5_path):
        raise RuntimeError("MD5_FILE_NOT_FOUND")
    print(md5_path)
    print(zip_path)
    expected = read_md5_file(md5_path)
    actual = calc_md5(zip_path)

    if expected != actual:
        raise RuntimeError("CHECKSUM_MISMATCH")


def write_version_file(product, series, zip_name, md5_value):
    version_dir = os.path.join(RUNTIME_ROOT, product, f"{product}_{series}")
    os.makedirs(version_dir, exist_ok=True)

    version_path = os.path.join(version_dir, "version.txt")

    content = [
        f"product={product}",
        f"series={series}",
        f"zip={zip_name}",
        f"md5={md5_value}",
        f"patched_at={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    ]

    with open(version_path, "w", encoding="utf-8") as f:
        f.write("\n".join(content))

def atomic_patch(product, series):
    zip_name = f"{product}_{series}.zip"
    zip_path = os.path.join(PATCH_CACHE, zip_name)

    tmp_dir = os.path.join(TMP_ROOT, f"{product}_{series}")
    final_dir = os.path.join(RUNTIME_ROOT, product, f"{product}_{series}")

    if not os.path.exists(zip_path):
        raise FileNotFoundError(zip_name)

    # 1️⃣ TMP clean
    if os.path.exists(tmp_dir):
        shutil.rmtree(tmp_dir)
    os.makedirs(tmp_dir, exist_ok=True)

    # 2️⃣ unzip to TMP
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(tmp_dir)

    expected_path = os.path.join(tmp_dir, product, f"{product}_{series}")
    if not os.path.exists(expected_path):
        raise RuntimeError("Invalid zip structure")

    # 3️⃣ prepare runtime parent
    os.makedirs(os.path.dirname(final_dir), exist_ok=True)

    # 4️⃣ atomic switch
    backup_dir = None
    if os.path.exists(final_dir):
        backup_dir = final_dir + "_bak_" + str(int(time.time()))
        os.rename(final_dir, backup_dir)

    try:
        os.rename(expected_path, final_dir)
    except Exception:
        if backup_dir and os.path.exists(backup_dir):
            os.rename(backup_dir, final_dir)
        raise

    # 5️⃣ cleanup
    if backup_dir and os.path.exists(backup_dir):
        shutil.rmtree(backup_dir)

    shutil.rmtree(tmp_dir)

    print(f"[OK] {product} / {series} Atomic Patch 완료")

if __name__ == "__main__":
    # patch_product("Tanami", "2025")

    # if is_process_running("A_Test.exe"):
    #     raise RuntimeError("Program is running")

    atomic_patch("Tanami", "2025")