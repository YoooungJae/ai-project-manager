# 출처: AI 프로젝트 매니저 최종보고서(2023.12) 부록 4에서 옮긴 코드입니다.
# PDF에서 옮기며 깨진 들여쓰기만 정리했고, 로직은 보고서 원문 그대로입니다. 원본 저장소는 남아 있지 않습니다.
import openai
from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Message
# 업로드 폼(Image)을 가져오는 import 줄은 보고서에 실려 있지 않아 생략했습니다.

# 각 페르소나에 대한 API 키 및 정보 설정
persona_data = {
    "Developer": {
        "api_key": "APIKEY",
        "details": {
            "age": 24,
            "innate": "analytical thinking, problem-solving skills, tech-savvy",
            "learned": "John Smith is someone who enjoys tackling complex problems through programming. He is always looking for innovative solutions.",
            "currently": "John Smith is currently working on a software development project and exploring new technologies.",
            "lifestyle": "John Smith usually goes to bed around midnight, wakes up around 8 am. He prefers a hearty breakfast and often works late into the evening.",
        },
    },
    "ProjectManager": {
        "api_key": "APIKEY",
        "details": {
            "age": 28,
            "innate": "organizational skills, leadership, project management experience",
            "learned": "Emily Davis is someone who enjoys diving into datasets to uncover meaningful insights. She has a strong passion for data analysis.",
            "currently": "Emily Davis is currently working on a data analysis project for a client and exploring new statistical models.",
            "lifestyle": "Emily Davis prefers early mornings and late nights. She starts her day with a quick jog and ends it with reviewing data trends.",
        },
    },
}

# 페르소나별 대화 히스토리를 따로 둔다 (에이전트끼리 기억을 공유하지 않도록)
persona_histories = {
    "Developer": [],
    "ProjectManager": [],
}

# 대화 최대 길이 (토큰 비용 때문에 6회로 제한)
max_conversation_length = 6
default_api_key = 'APIKEY'


def get_completion(prompt, persona):
    persona_info = persona_data.get(persona, {"api_key": "default_api_key", "details": {}})
    api_key = persona_info["api_key"]
    persona_details = persona_info["details"]

    persona_histories[persona].append({"role": "user", "content": prompt})

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": f"You are a helpful assistant for {persona}. {persona_details['learned']}"},
            *persona_histories[persona],
        ],
        max_tokens=150,
        stop=None,
        api_key=api_key,
    )
    reply = response['choices'][0]['message']['content']

    # 대화가 최대 길이에 도달하면 대화를 끝내고 히스토리를 초기화
    conversation_length = len(response['choices'][0]['message']['content'].split('\n'))
    if conversation_length >= max_conversation_length:
        reply += "\n\n[Conversation Ended]"
        persona_histories[persona] = []
    return reply


def index(request):
    return render(request, 'chat/index.html')


def room(request, room_name):
    username = request.GET.get('username', 'Anonymous')
    messages = Message.objects.filter(room=room_name)[0:25]
    return render(request, 'chat/room.html', {'room_name': room_name, 'username': username, 'messages': messages})


def upload_image(request):
    if request.method == 'POST':
        form = Image(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('success_page')
    else:
        form = Image()
    return render(request, 'upload_image.html', {'form': form})


def query_view(request):
    if request.method == 'POST':
        user_input = str(request.POST.get('prompt'))
        conversation = []
        # "Ai 야"로 시작하는 경우에만 에이전트끼리 토론을 시작
        if user_input.startswith("Ai 야 "):
            prompt = user_input[4:]
            for _ in range(max_conversation_length):
                response_ai1 = get_completion(prompt, "Developer")
                conversation.append({"role": "Ai1 (Developer)", "content": response_ai1})
                prompt = response_ai1  # Ai2가 Ai1의 답변에 대해 토론
                response_ai2 = get_completion(prompt, "ProjectManager")
                conversation.append({"role": "Ai2 (ProjectManager)", "content": response_ai2})
                prompt = response_ai2  # Ai1이 Ai2의 답변에 대해 토론
            conversation.append({"role": "system", "content": "[Conversation Ended]"})
        return JsonResponse({'responses': conversation})
    elif request.method == 'GET':
        return render(request, 'room.html')
    return JsonResponse({'error': '잘못된 요청입니다.'})
