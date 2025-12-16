import csv
import json
import random
from datetime import date, timedelta





# 파일 이름들 위에 모아서 여기다 적기
WORDS_FILE = "words.csv"         # 단어장 저장(영단어, 뜻)
PROGRESS_FILE = "progress.json" # 단어별 복습 날짜/연속정답/오답횟수 저장
ATTEMPTS_FILE = "attempts.csv"  # 퀴즈 기록 저장(통계용)







# -----------------------------
# 1) 파일 관련 함수들
# -----------------------------
def load_progress():
    """
    progress.json을 읽어서 dict로 가져오는 함수.
    파일이 없으면 빈 dict로 시작하게.
    """
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # 처음 실행이면 progress.json이 없을 수 있어서 예외 처리
        return {}





def save_progress(progress):
    """
    progress dict를 progress.json에 저장.
    """
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)




def ensure_files_exist():
    """
    프로그램 처음 실행했을 때 파일 없으면 만들어주는 함수..
    """

    # words.csv 없으면 헤더만 만들기
    try:
        with open(WORDS_FILE, "r", encoding="utf-8") as _:
            pass

        
    except FileNotFoundError:
        with open(WORDS_FILE, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["word", "meaning"])

    # attempts.csv 없으면 헤더만 만들기
    try:
        
        with open(ATTEMPTS_FILE, "r", encoding="utf-8") as _:
            
            pass
        
    except FileNotFoundError:
        with open(ATTEMPTS_FILE, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["date", "word", "is_correct", "user_answer"])

    # progress.json은 load 했다가 다시 저장하면 파일 생성
    progress = load_progress()
    save_progress(progress)



    


def load_words():
    """
    words.csv를 읽어서 [{"word":..., "meaning":...}, ...] 형태로 반환.
    """
    words = []
    
    with open(WORDS_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            w = row["word"].strip()
            m = row["meaning"].strip()
            
            if w != "":
                words.append({"word": w, "meaning": m})
                
    return words






def append_word(word, meaning):
    """
    words.csv 맨 아래에 단어 한 줄 추가.
    """
    with open(WORDS_FILE, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([word.strip(), meaning.strip()])



        


def log_attempt(word, is_correct, user_answer):
    """
    퀴즈 결과를 attempts.csv에 저장.
    나중에 stats에서 정답률 계산하려고 남겨두는 용도.
    """
    with open(ATTEMPTS_FILE, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([str(date.today()), word, int(is_correct), user_answer])






# -----------------------------
# 2) 복습 관련 함수들
# -----------------------------
def init_word_in_progress(progress, word):
    """
    progress에 단어가 없으면 기본값 넣기.
    초기에 next_review를 오늘로 잡아두면 바로 today/quiz에 뜨게.
    """
    if word not in progress:
        progress[word] = {
            "next_review": str(date.today()),
            "streak": 0,
            "wrong_count": 0
        }






def get_due_words(words, progress):
    """
    오늘 복습할 단어만 골라내기.
    next_review 날짜가 오늘 이하이면 due에 포함.
    """
    today = date.today()
    due = []

    for item in words:
        w = item["word"]
        init_word_in_progress(progress, w)  # 혹시 진행정보가 없으면 만들어두기
        next_date = date.fromisoformat(progress[w]["next_review"])
        if next_date <= today:
            due.append(item)

    return due





def update_schedule(progress, word, correct):
    """
    맞으면 복습 간격을 조금 늘리고, 틀리면 내일 다시 보게 하도록...?.
        """
    p = progress[word]

    if correct:
        p["streak"] += 1

        # streak에 따라 간격 늘리기 (1,2,4,7일 느낌)
        if p["streak"] == 1:
            days = 1
        elif p["streak"] == 2:
            days = 2
        elif p["streak"] == 3:
            days = 4
        else:
            days = 7

        p["next_review"] = str(date.today() + timedelta(days=days))

    else:
        p["wrong_count"] += 1
        p["streak"] = 0
        p["next_review"] = str(date.today() + timedelta(days=1))





# -----------------------------
# 3) 명령어 기능모음
# -----------------------------
def show_help():
    print("""
Commands:
  add     : 단어 추가(중복이면 추가 안 함)
  list    : 전체 단어 보기
  today   : 오늘 복습 단어 보기
  quiz    : 퀴즈 (뜻 -> 단어)
  stats   : 통계
  remove  : 특정 단어 삭제
  reset   : 단어장/기록 전체 초기화
  help    : 명령어 보기
  exit    : 종료
""")




def cmd_add(words, progress):
    word = input("word: ").strip()
    meaning = input("meaning: ").strip()

    if word == "":
        print("단어가 비었어. 다시 해줘!")
        return words, progress

    # 중복 방지: 대소문자 무시해서 체크
    for item in words:
        if item["word"].lower() == word.lower():
            print(f"⚠️ 중복이야! 이미 '{item['word']}'가 단어장에 있어. 이건 추가하지 않을게!")
            print(f"   기존 뜻: {item['meaning']}")
            return words, progress

    # 중복 아니면 저장
    append_word(word, meaning)

    # progress도 같이 초기화
    init_word_in_progress(progress, word)
    save_progress(progress)

    print(f"Added: {word} - {meaning}")

    # words를 다시 불러오는 게 깔끔해보임...
    words = load_words()
    return words, progress






def cmd_list(words):
    
    if len(words) == 0:
        print("단어장이 비어있어.")
        return

    print("\n[All Words]")

    for i, item in enumerate(words, start=1):
        print(f"{i}. {item['word']} - {item['meaning']}")





def cmd_today(words, progress):
    
    due = get_due_words(words, progress)

    if len(due) == 0:
        print("오늘 복습할 단어가 없어!")
        return

    print("\n[Today Due Words]")

    for item in due[:20]:
        w = item["word"]
        m = item["meaning"]
        p = progress[w]
        print(f"- {w} : {m}  (next={p['next_review']}, streak={p['streak']})")



        


def cmd_quiz(words, progress, n=10):

    due = get_due_words(words, progress)
    
    if len(due) == 0:
        print("오늘 복습할 단어가 없어. add로 단어를 넣거나 내일 다시!")
        return words, progress

    random.shuffle(due)

    print("\n[Quiz: meaning -> word] (type 'q' to quit)")
    for item in due[:min(n, len(due))]:
        word = item["word"]
        meaning = item["meaning"]

        ans = input(f"뜻: {meaning}  단어는? ").strip()
        
        if ans.lower() == "q":
            break

        correct = (ans.lower() == word.lower())
        if correct:
            print("✅ Correct")
            
        else:
            print(f"❌ Wrong  (answer: {word})")

        # 기록 저장 + 복습 스케줄 업데이트
        log_attempt(word, correct, ans)
        update_schedule(progress, word, correct)

    save_progress(progress)
    print("Quiz finished.")
    return words, progress






def cmd_stats(progress):
    total = 0
    correct = 0

    with open(ATTEMPTS_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            correct += int(row["is_correct"])

    print("\n[Stats]")
    if total == 0:
        print("- 아직 퀴즈 기록이 없어.")
    else:
        print(f"- Overall accuracy: {correct/total*100:.1f}% ({correct}/{total})")

    # progress의 wrong_count로 많이 틀린 단어 Top 보여주기
    wrong_list = []
    for w, p in progress.items():
        if p.get("wrong_count", 0) > 0:
            wrong_list.append((w, p["wrong_count"]))

    wrong_list.sort(key=lambda x: x[1], reverse=True)
    if len(wrong_list) > 0:
        print("- Most wrong words:")
        for w, cnt in wrong_list[:10]:
            print(f"  * {w}: {cnt}")







def rewrite_csv_without_word(path, header, target_word, key_name):
    """
    CSV에서 특정 단어를 제외하고 다시 저장하는 함수.
    remove 기능 만들 때 다시 사용하려고 새로 빼놓음
    """
    target = target_word.strip().lower()
    rows = []

    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            if row[key_name].strip().lower() != target:
                rows.append(row)

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)







def cmd_remove(words, progress):
    target = input("삭제할 단어(word): ").strip()
    if target == "":
        print("단어가 비었어.")
        return words, progress

    existed = any(item["word"].lower() == target.lower() for item in words)

    # words.csv에서 삭제
    rewrite_csv_without_word(WORDS_FILE, ["word", "meaning"], target, "word")
    # attempts.csv에서도 삭제
    rewrite_csv_without_word(ATTEMPTS_FILE, ["date", "word", "is_correct", "user_answer"], target, "word")

    # progress에서 삭제(대소문자 무시)
    for k in list(progress.keys()):
        if k.lower() == target.lower():
            del progress[k]
            break
    save_progress(progress)

    # words 다시 로드
    words = load_words()

    if existed:
        print(f"✅ Removed: {target}")
    else:
        print(f"⚠️ '{target}'를 단어장에서 찾지 못했어.")
    return words, progress







def cmd_reset():
    print("⚠️ 단어장/진행상황/퀴즈기록이 전부 삭제됩니다.")
    confirm = input("정말 초기화할까요? YES를 입력하면 진행: ").strip()
    if confirm != "YES":
        print("취소됨.")
        return

    # words.csv 초기화
    with open(WORDS_FILE, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerow(["word", "meaning"])

    # attempts.csv 초기화
    with open(ATTEMPTS_FILE, "w", encoding="utf-8", newline="") as f:
        csv.writer(f).writerow(["date", "word", "is_correct", "user_answer"])

    # progress.json 초기화
    save_progress({})

    print("✅ 초기화 완료.")




    


# -----------------------------
# 4) main
# -----------------------------
def main():
    ensure_files_exist()

    words = load_words()
    progress = load_progress()

    # 단어가 이미 있으면 progress에도 기본값을 채워주기
    for item in words:
        init_word_in_progress(progress, item["word"])
    save_progress(progress)

    print("=== 영단어 학습봇 (Simple) ===")
    show_help()

    while True:
        cmd = input("\n> ").strip().lower()

        if cmd == "add":
            words, progress = cmd_add(words, progress)
        elif cmd == "list":
            cmd_list(words)
        elif cmd == "today":
            cmd_today(words, progress)
        elif cmd == "quiz":
            words, progress = cmd_quiz(words, progress, n=10)
        elif cmd == "stats":
            cmd_stats(progress)
        elif cmd == "remove":
            words, progress = cmd_remove(words, progress)
        elif cmd == "reset":
            cmd_reset()
            words = load_words()
            progress = load_progress()
        elif cmd == "help":
            show_help()
        elif cmd == "exit":
            print("수고했어, 단어시험 잘 봐!")
            break
        else:
            print("Unknown command. Type 'help'.")


if __name__ == "__main__":
    main()
