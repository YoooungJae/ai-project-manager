# 출처: AI 프로젝트 매니저 최종보고서(2023.12) 부록 4에서 옮긴 코드입니다.
# PDF에서 옮기며 깨진 들여쓰기만 정리했고, 로직은 보고서 원문 그대로입니다.
# 사람끼리의 채팅과 "Ai 야"로 시작하는 에이전트 호출을 한 채팅방(WebSocket)에서 구분해 처리합니다.
import json
import openai
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Message
from .views import persona_data, default_api_key, max_conversation_length

openai.api_key = 'APIKEY'


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"chat_{self.room_name}"
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        username = data['username']
        room = data['room']

        if message.strip().startswith("Ai 야"):
            ai1_responses = []
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'chat.message', 'message': message, 'username': username,
                'ai_response1': None, 'ai_response2': None,
            })
            for _ in range(5):  # 최대 5번 반복
                ai_response1 = await self.get_ai_completion(message, "Developer")
                await self.save_message('Ai1', room, message, ai_response1, None)
                await self.channel_layer.group_send(self.room_group_name, {
                    'type': 'chat.message', 'message': ai_response1, 'username': 'Ai1',
                    'ai_response1': ai_response1, 'ai_response2': None,
                })

                ai_response2 = await self.get_ai_completion(ai_response1, "ProjectManager")
                await self.save_message('Ai2', room, ai_response1, ai_response2, None)
                await self.channel_layer.group_send(self.room_group_name, {
                    'type': 'chat.message', 'message': ai_response2, 'username': 'Ai2',
                    'ai_response1': None, 'ai_response2': ai_response2,
                })
                message = ai_response2

            # 대화가 끝나면 Ai1이 토론 내용을 정리해 한 번만 채팅으로 전송
            ai_response1 = await self.get_ai_completion('\n'.join(ai1_responses) + " Summary and Conclusion", "Developer")
            await self.save_message('Ai1', room, ai_response1, None, None)
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'chat.message', 'message': ai_response1, 'username': 'Ai1',
                'ai_response1': None, 'ai_response2': None,
            })
        else:
            # 일반 메시지는 그대로 같은 방 사용자들에게 전송
            await self.save_message(username, room, message, None, None)
            await self.channel_layer.group_send(self.room_group_name, {
                'type': 'chat.message', 'message': message, 'username': username,
                'ai_response1': None, 'ai_response2': None,
            })

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'username': event['username'],
            'ai_response1': event['ai_response1'],
            'ai_response2': event['ai_response2'],
        }))

    async def get_ai_completion(self, prompt, persona):
        persona_info = persona_data.get(persona, {"api_key": default_api_key, "details": {}})
        query = await sync_to_async(openai.ChatCompletion.create)(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are a helpful assistant for {persona}. {persona_info['details']['learned']}"},
                {"role": "user", "content": prompt},
            ],
            max_tokens=150, n=1, stop=None, temperature=0.7,
            api_key=persona_info["api_key"],
        )
        return query.choices[0].message["content"]

    @sync_to_async
    def save_message(self, username, room, message, ai_response1, ai_response2):
        Message.objects.create(username=username, room=room, content=message,
                               ai_response1=ai_response1, ai_response2=ai_response2)
