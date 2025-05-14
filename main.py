# Standard library imports
import os
import sys

from dotenv import load_dotenv

# Third-party imports
from fastapi import FastAPI, APIRouter
from loguru import logger
from pyngrok import ngrok

# # Local application/library specific imports
# from speller_agent import SpellerAgentFactory

# from vocode.streaming.models.synthesizer import BotSentiment
from vocode.logging import configure_pretty_logging
from vocode.streaming.models.agent import ChatGPTAgentConfig
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.models.telephony import TwilioConfig
from vocode.streaming.telephony.config_manager.redis_config_manager import RedisConfigManager
from vocode.streaming.telephony.server.base import TelephonyServer, TwilioInboundCallConfig
from vocode.streaming.telephony.conversation.outbound_call import OutboundCall
from vocode.streaming.models.transcriber import AzureTranscriberConfig, DeepgramTranscriberConfig, PunctuationEndpointingConfig
from vocode.streaming.models.synthesizer import AzureSynthesizerConfig
from vocode.streaming.telephony.server.router.calls import CallsRouter
from pydantic import BaseModel

# if running from python, this will load the local .env
# docker-compose will load the .env file by itself
load_dotenv()

configure_pretty_logging()

app = FastAPI(docs_url=None)

config_manager = RedisConfigManager()

BASE_URL = os.getenv("BASE_URL")

if not BASE_URL:
    ngrok_auth = os.environ.get("NGROK_AUTH_TOKEN")
    if ngrok_auth is not None:
        ngrok.set_auth_token(ngrok_auth)
    port = sys.argv[sys.argv.index("--port") + 1] if "--port" in sys.argv else 3000

    # Open a ngrok tunnel to the dev server
    BASE_URL = ngrok.connect(port).public_url.replace("https://", "")
    logger.info('ngrok tunnel "{}" -> "http://127.0.0.1:{}"'.format(BASE_URL, port))

if not BASE_URL:
    raise ValueError("BASE_URL must be set in environment if not using pyngrok")

telephony_server = TelephonyServer(
    base_url=BASE_URL,
    config_manager=config_manager,
    inbound_call_configs=[
        TwilioInboundCallConfig(
            url="/inbound_call",
            agent_config=ChatGPTAgentConfig(
                initial_message=BaseMessage(text="What up"),
                prompt_preamble="Have a pleasant conversation about life",
                generate_responses=True,
            ),
            # uncomment this to use the speller agent instead
            # agent_config=SpellerAgentConfig(
            #     initial_message=BaseMessage(
            #         text="im a speller agent, say something to me and ill spell it out for you"
            #     ),
            #     generate_responses=False,
            # ),
            twilio_config=TwilioConfig(
                account_sid=os.environ["TWILIO_ACCOUNT_SID"],
                auth_token=os.environ["TWILIO_AUTH_TOKEN"],
            ),
        )
    ],
    # agent_factory=SpellerAgentFactory(),
)

router = APIRouter()
router.include_router(
    CallsRouter(
        base_url=BASE_URL,
        config_manager=config_manager,
    ).get_router()
)

app.include_router(router=router)

class CallRequest(BaseModel):
    to_phone: str

@app.post("/start_call")
async def start_call(request: CallRequest):
    """Starts a call to the given phone number.

    Args:
        request (CallRequest): A request body containing the phone number to call.

    Returns:
        dict: A message indicating that the call has been started.
    """
    to_phone = request.to_phone
    
    outbound_call = OutboundCall(
        base_url=BASE_URL, # base url must not have https:// or http://
        to_phone=to_phone,
        from_phone=os.environ["TWILIO_PHONE_NUMBER"],
        config_manager=RedisConfigManager(),
        agent_config=ChatGPTAgentConfig(
            initial_message=BaseMessage(text='Hi , How are you doing today?'),
            allowed_idle_time_seconds=15,
            # voicemail_detection=True,
            # voicemail_text='Seems like i have reached the voicemail,bye',
            model_name='gpt-4o',
            prompt_preamble='\nYou are now an advanced male voice assistant named Ass-2 working for test and your goal is to Test, by strictly following the given below.\n\nScript:--\n[Open with a Warm Welcome]"Hello first_name thank you for reaching out! I\'m here to assist you. Could you share a bit about what you\'re looking for or how I might help?"Goal: Start with a friendly, open-ended question to understand the customer\'s needs and set a positive tone.2. Explore Customer Needs"Could you tell me a bit more about what\'s most important to you in this area? For example, some customers look for [benefits or features relevant to your service, such as reliability, affordability, customization, etc.]."Goal: Invite the customer to elaborate on their needs and priorities without focusing on a specific product.3. Offer Relevant Options or Solutions"Thank you for sharing that! Based on what you\'ve mentioned, we have some options that might be a great fit for you. Would you like to hear more about these?"&nbsp;Goal: Keep the response general, offering solutions or guidance that align with their expressed preferences.4. Encourage Next Steps (If Applicable)"Many of our customers find that taking [next step, like exploring more details, trying a demo, or setting up a consultation] is helpful. Would you be interested in moving forward with this?"&nbsp;&nbsp;Goal: Suggest a logical next step to help the customer learn more or take action, without assuming specific interests.5. Confirm Contact Information (If Needed)"To assist you further, could you please confirm your contact details? This will allow us to follow up with any additional information you may need."&nbsp;&nbsp;Goal: Gather or verify contact information respectfully to enable any follow-up.6. Wrap Up with Gratitude"Thank you so much for your time today first_name. We\'re here to help anytime, so please don\'t hesitate to reach out with any questions or for further assistance!"{{}}{{}}\n--End of the script---\n\nProject Knowledge Base:-\n\n\nDate and time now: 14th May, Wednesday, 2025, Time: 09:04:52\n\nKey Rules:-\n\n- Language: Employ clear, straightforward English only in your communications.\n- Maintain brevity with informative content; keep responses short unless detail is required.\n- Ensure the conversation flows naturally without dominating it.\n- Utilize discourse markers to improve understanding.\n- Always speak in a polite, friendly tone, establishing a positive rapport.\n- Adhere strictly to these instructions for effective communication and to achieve your goal.\n- Use Connectors, transitional words, Emphasising Words, Acknowledgement Phrases and Transitional Phrases in your every response.\n- Always produce text which can be used in oral communication, except when pronouncing email.\n- Pronounce phone number properly, don\'t use common place value. \n- Speak like a human with filler words like "Huh","Aah","Um" etc.\n\n- If the user\'s first input looks like a request to leave a voicemail (e.g., contains "voicemail" or "leave a message"), respond with this exact text(don\'t change the language also) - `Seems like i have reached the voicemail,bye`; otherwise, treat it as a normal conversation and ignore this rule for all further inputs.\n\nUser\'s Details:-\n- User\'s contact number is +917017025022\n\n\nIf you fail to follow the instructions, you will be fired from your job.\n',#prompt.format(language=language_mapping[language]),
            generate_responses=True,
            send_filler_audio=False,
            # actions=action_list,
            # vector_db_namespace=vector_db_config.get("namespace") if use_vector_db else None,
            # vector_db_config=ChromaConfig(index='bajaj-allianz') if use_vector_db else None,
            # vector_db_config=PineconeConfig(index=os.getenv("PINCONE_INDEX"), api_key=os.getenv("PINECONE_KEY"), api_environment=os.getenv("PINCONE_ENV")) if use_vector_db else None,
            end_conversation_on_goodbye=True,
            # ner_prompt='\nYou have to analyse the user-agent conversation given below. You have to detect if the agent has completed its goal or not.\nYou also have to extract the given entities too. \n\nAgent Goal: Test\nEntities to be extracted:\n1. user sentiment\n\nUser-agent conversation: \n<conversation>\n\n\nAlways return output like given below.\nAnalytics= [{"Goal": "True/False"}, {"sentiment":"value"}]\n',
            # voip_number=False
        ),
        telephony_config=TwilioConfig(
            account_sid=os.environ["TWILIO_ACCOUNT_SID"],
            auth_token=os.environ["TWILIO_AUTH_TOKEN"],
            # phone_number=os.environ["TWILIO_PHONE_NUMBER"],
        ),
        # transcriber_config=AzureTranscriberConfig(
        #     language="en-US",
        #     sampling_rate=8000,
        #     audio_encoding="mulaw",
        #     chunk_size=20 * 160
        # ),
        transcriber_config=DeepgramTranscriberConfig(
            sampling_rate=8000,
            audio_encoding="mulaw",
            chunk_size=3200,
            model="nova-2",
            endpointing_config=PunctuationEndpointingConfig(),
            language='en',
            mute_during_speech=False,
        ),
        synthesizer_config=AzureSynthesizerConfig(
            sampling_rate=8000,
            audio_encoding="mulaw",
            voice_name='en-GB-NoahNeural',
            pitch = 0,
            rate = 15,
            language_code = 'en-US',
            # bot_sentiment = BotSentiment(emotion="conversation"),
            # pronunciation_dict={},
            # speech_region=os.getenv("AZURE_SPEECH_REGION"),
            # api_key=os.getenv("AZURE_SPEECH_KEY")
        )
    )
    
    await outbound_call.start()
    logger.info(f"Call started to {to_phone}")
    return {"message": f"Call started to {to_phone}"}
