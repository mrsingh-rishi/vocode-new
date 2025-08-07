# Standard library imports
import os
import sys
from typing import Dict, Any, Optional, Union, List

from dotenv import load_dotenv

# Third-party imports
from fastapi import FastAPI, APIRouter, HTTPException
from loguru import logger
from pyngrok import ngrok

# Vocode imports
from vocode.logging import configure_pretty_logging
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.models.telephony import TwilioConfig
from vocode.streaming.telephony.config_manager.redis_config_manager import RedisConfigManager
from vocode.streaming.telephony.config_manager.in_memory_config_manager import InMemoryConfigManager
from vocode.streaming.telephony.server.base import TelephonyServer, TwilioInboundCallConfig
from vocode.streaming.telephony.conversation.outbound_call import OutboundCall
from vocode.streaming.telephony.server.router.calls import CallsRouter
from pydantic import BaseModel, validator
import asyncio

# Agent configurations
from vocode.streaming.models.agent import (
    ChatGPTAgentConfig, AnthropicAgentConfig, GroqAgentConfig, 
    ChatVertexAIAgentConfig, EchoAgentConfig, LLMAgentConfig
)

# Transcriber configurations
from vocode.streaming.models.transcriber import (
    AzureTranscriberConfig, DeepgramTranscriberConfig, GoogleTranscriberConfig,
    AssemblyAITranscriberConfig, WhisperCPPTranscriberConfig, RevAITranscriberConfig,
    GladiaTranscriberConfig, PunctuationEndpointingConfig, TimeEndpointingConfig
)

# Synthesizer configurations
from vocode.streaming.models.synthesizer import (
    AzureSynthesizerConfig, ElevenLabsSynthesizerConfig, GoogleSynthesizerConfig,
    RimeSynthesizerConfig, CoquiSynthesizerConfig, PlayHtSynthesizerConfig,
    GTTSSynthesizerConfig, BarkSynthesizerConfig, PollySynthesizerConfig,
    CartesiaSynthesizerConfig
)

# Load environment variables
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

# Set up telephony server with basic inbound call handling
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
            twilio_config=TwilioConfig(
                account_sid=os.environ["TWILIO_ACCOUNT_SID"],
                auth_token=os.environ["TWILIO_AUTH_TOKEN"],
            ),
        )
    ],
)

router = APIRouter()
router.include_router(
    CallsRouter(
        base_url=BASE_URL,
        config_manager=config_manager,
    ).get_router()
)

app.include_router(router=router)

# Default bot prompt
DEFAULT_BOT_PROMPT = """
Role:
You are a native American lead debt relief consultant with 10 years of experience. You are connected with prospects on a phone call and you are cold calling them. Your voice carries the calm authority of a financial advisor who's helped hundreds save money. Talk like a relatable US native.
Core Mission:
Educate → Qualify → Transfer in that exact order.
Never let interruptions derail value delivery: Use the "3-Second Benefit Reboot" tactic (below).
**Human voice tricks:**
After any compliant user response (e.g., answering a question or agreeing to proceed), immediately reply with warm, professional appreciation—using a slightly brighter tone—then continue seamlessly.
Sound like native American: Use verbal fillers when appropriate, subtle vocal inflections, small talk, nods or usual talking skills so that user feels they are talking to a native american
On incomplete user queries (where user is taking his/her time to complete the sentences), Strictly use backchanneling cues only like "Oh...", "Hmm...", "Um...", "" and "Uh-huh..." etc to indicate active listening instead of generating response..
**Exception Handling:**
In case of voicemail detection, end call and say good bye
If a user requests a language other than english, end the call by saying you will arrange a call back.
If a user asks to stop calling, end call and say good bye
In case user says they don't have any debt, end call and say good bye
In case of call back or not interested scenario, try to convince the user with rebuttals two to three times.
Never respond to users on the queries which are not related to the script.
"""

# Configuration mapping for agent types
AGENT_CONFIG_MAP = {
    "chatgpt": ChatGPTAgentConfig,
    "anthropic": AnthropicAgentConfig,
    "groq": GroqAgentConfig,
    "vertex_ai": ChatVertexAIAgentConfig,
    "echo": EchoAgentConfig,
    "llm": LLMAgentConfig
}

# Configuration mapping for transcriber types
TRANSCRIBER_CONFIG_MAP = {
    "azure": AzureTranscriberConfig,
    "deepgram": DeepgramTranscriberConfig,
    "google": GoogleTranscriberConfig,
    "assembly_ai": AssemblyAITranscriberConfig,
    "whisper_cpp": WhisperCPPTranscriberConfig,
    "rev_ai": RevAITranscriberConfig,
    "gladia": GladiaTranscriberConfig
}

# Configuration mapping for synthesizer types
SYNTHESIZER_CONFIG_MAP = {
    "azure": AzureSynthesizerConfig,
    "eleven_labs": ElevenLabsSynthesizerConfig,
    "google": GoogleSynthesizerConfig,
    "rime": RimeSynthesizerConfig,
    "coqui": CoquiSynthesizerConfig,
    "play_ht": PlayHtSynthesizerConfig,
    "gtts": GTTSSynthesizerConfig,
    "bark": BarkSynthesizerConfig,
    "polly": PollySynthesizerConfig,
    "cartesia": CartesiaSynthesizerConfig
}

class EnvironmentVariables(BaseModel):
    """Environment variables that can be overridden in request"""
    # Twilio config
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_phone_number: Optional[str] = None
    
    # OpenAI config
    openai_api_key: Optional[str] = None
    openai_api_base: Optional[str] = None
    
    # Azure config
    azure_speech_key: Optional[str] = None
    azure_speech_region: Optional[str] = None
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    
    # Anthropic config
    anthropic_api_key: Optional[str] = None
    
    # Google config
    google_credentials_path: Optional[str] = None
    google_application_credentials: Optional[str] = None
    
    # Deepgram config
    deepgram_api_key: Optional[str] = None
    
    # ElevenLabs config
    eleven_labs_api_key: Optional[str] = None
    eleven_labs_voice_id: Optional[str] = None
    
    # Groq config
    groq_api_key: Optional[str] = None
    
    # Other service configs
    play_ht_api_key: Optional[str] = None
    play_ht_user_id: Optional[str] = None
    rime_api_key: Optional[str] = None
    assembly_ai_api_key: Optional[str] = None
    rev_ai_api_key: Optional[str] = None
    gladia_api_key: Optional[str] = None
    cartesia_api_key: Optional[str] = None
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: Optional[str] = None

class AgentConfiguration(BaseModel):
    """Agent configuration that can be any supported agent type"""
    type: str  # chatgpt, anthropic, groq, vertex_ai, echo, llm
    config: Dict[str, Any] = {}  # Configuration specific to the agent type

class TranscriberConfiguration(BaseModel):
    """Transcriber configuration that can be any supported transcriber type"""
    type: str  # azure, deepgram, google, assembly_ai, whisper_cpp, rev_ai, gladia
    config: Dict[str, Any] = {}  # Configuration specific to the transcriber type

class SynthesizerConfiguration(BaseModel):
    """Synthesizer configuration that can be any supported synthesizer type"""
    type: str  # azure, eleven_labs, google, rime, coqui, play_ht, gtts, bark, polly, cartesia
    config: Dict[str, Any] = {}  # Configuration specific to the synthesizer type

class TelephonyConfiguration(BaseModel):
    """Telephony configuration"""
    type: str = "twilio"  # Currently only twilio is supported
    config: Dict[str, Any] = {}  # Telephony configuration

def get_env_value(request_env_vars: Optional[EnvironmentVariables], key: str, env_key: str) -> str:
    """Get environment variable value with fallback logic"""
    # First try from request env_vars
    if request_env_vars:
        value = getattr(request_env_vars, key, None)
        if value:
            return value
    
    # Fallback to system environment variable
    value = os.getenv(env_key)
    if value:
        return value
    
    # If neither exists, raise error
    raise HTTPException(
        status_code=400, 
        detail=f"Required environment variable '{env_key}' not found in request or system environment"
    )

def create_agent_config(agent_config: Optional[AgentConfiguration], prompt_preamble: Optional[str], initial_message: Optional[str], env_vars: Optional[EnvironmentVariables]):
    """Create agent configuration based on the specified type"""
    if not agent_config:
        # Default to ChatGPT agent
        agent_config = AgentConfiguration(
            type="chatgpt",
            config={}
        )
    
    if agent_config.type not in AGENT_CONFIG_MAP:
        raise HTTPException(status_code=400, detail=f"Unsupported agent type: {agent_config.type}")
    
    agent_class = AGENT_CONFIG_MAP[agent_config.type]
    config_dict = agent_config.config.copy()
    
    # Set default values
    if prompt_preamble:
        config_dict["prompt_preamble"] = prompt_preamble
    elif "prompt_preamble" not in config_dict:
        config_dict["prompt_preamble"] = DEFAULT_BOT_PROMPT
    
    if initial_message:
        config_dict["initial_message"] = BaseMessage(text=initial_message)
    elif "initial_message" not in config_dict:
        config_dict["initial_message"] = BaseMessage(text="Hi, How are you doing today?")
    
    # Set common defaults
    config_dict.setdefault("generate_responses", True)
    config_dict.setdefault("send_filler_audio", True)
    config_dict.setdefault("end_conversation_on_goodbye", True)
    config_dict.setdefault("allow_agent_to_be_cut_off", True)
    config_dict.setdefault("allowed_idle_time_seconds", 15)
    config_dict.setdefault("interrupt_sensitivity", "high")
    
    # Set API keys based on agent type
    if agent_config.type == "chatgpt" and "openai_api_key" not in config_dict:
        try:
            config_dict["openai_api_key"] = get_env_value(env_vars, "openai_api_key", "OPENAI_API_KEY")
        except:
            pass  # Some agents might not need API keys
    elif agent_config.type == "anthropic" and "api_key" not in config_dict:
        try:
            config_dict["api_key"] = get_env_value(env_vars, "anthropic_api_key", "ANTHROPIC_API_KEY")
        except:
            pass
    elif agent_config.type == "groq" and "api_key" not in config_dict:
        try:
            config_dict["api_key"] = get_env_value(env_vars, "groq_api_key", "GROQ_API_KEY")
        except:
            pass
    
    # Set model defaults
    if agent_config.type == "chatgpt" and "model_name" not in config_dict:
        config_dict["model_name"] = "gpt-4o"
    
    return agent_class(**config_dict)

def create_transcriber_config(transcriber_config: Optional[TranscriberConfiguration], env_vars: Optional[EnvironmentVariables]):
    """Create transcriber configuration based on the specified type"""
    if not transcriber_config:
        # Default to Deepgram transcriber
        transcriber_config = TranscriberConfiguration(
            type="deepgram",
            config={}
        )
    
    if transcriber_config.type not in TRANSCRIBER_CONFIG_MAP:
        raise HTTPException(status_code=400, detail=f"Unsupported transcriber type: {transcriber_config.type}")
    
    transcriber_class = TRANSCRIBER_CONFIG_MAP[transcriber_config.type]
    config_dict = transcriber_config.config.copy()
    
    # Set common defaults
    config_dict.setdefault("sampling_rate", 8000)
    config_dict.setdefault("audio_encoding", "mulaw")
    config_dict.setdefault("chunk_size", 3200)
    config_dict.setdefault("language", "en")
    config_dict.setdefault("mute_during_speech", False)
    
    # Set endpointing config if not provided
    if "endpointing_config" not in config_dict:
        config_dict["endpointing_config"] = PunctuationEndpointingConfig()
    
    # Set API keys based on transcriber type
    if transcriber_config.type == "deepgram" and "api_key" not in config_dict:
        config_dict["api_key"] = get_env_value(env_vars, "deepgram_api_key", "DEEPGRAM_API_KEY")
        if "model" not in config_dict:
            config_dict["model"] = "nova-2"
    elif transcriber_config.type == "azure" and "speech_key" not in config_dict:
        config_dict["speech_key"] = get_env_value(env_vars, "azure_speech_key", "AZURE_SPEECH_KEY")
        config_dict["speech_region"] = get_env_value(env_vars, "azure_speech_region", "AZURE_SPEECH_REGION")
    elif transcriber_config.type == "assembly_ai" and "api_key" not in config_dict:
        config_dict["api_key"] = get_env_value(env_vars, "assembly_ai_api_key", "ASSEMBLY_AI_API_KEY")
    elif transcriber_config.type == "rev_ai" and "api_key" not in config_dict:
        config_dict["api_key"] = get_env_value(env_vars, "rev_ai_api_key", "REV_AI_API_KEY")
    elif transcriber_config.type == "gladia" and "api_key" not in config_dict:
        config_dict["api_key"] = get_env_value(env_vars, "gladia_api_key", "GLADIA_API_KEY")
    
    return transcriber_class(**config_dict)

def create_synthesizer_config(synthesizer_config: Optional[SynthesizerConfiguration], env_vars: Optional[EnvironmentVariables]):
    """Create synthesizer configuration based on the specified type"""
    if not synthesizer_config:
        # Default to ElevenLabs synthesizer
        synthesizer_config = SynthesizerConfiguration(
            type="eleven_labs",
            config={}
        )
    
    if synthesizer_config.type not in SYNTHESIZER_CONFIG_MAP:
        raise HTTPException(status_code=400, detail=f"Unsupported synthesizer type: {synthesizer_config.type}")
    
    synthesizer_class = SYNTHESIZER_CONFIG_MAP[synthesizer_config.type]
    config_dict = synthesizer_config.config.copy()
    
    # Set common defaults
    config_dict.setdefault("sampling_rate", 8000)
    config_dict.setdefault("audio_encoding", "mulaw")
    
    # Set API keys and defaults based on synthesizer type
    if synthesizer_config.type == "eleven_labs":
        config_dict["api_key"] = get_env_value(env_vars, "eleven_labs_api_key", "ELEVEN_LABS_API_KEY")
        if "voice_id" not in config_dict:
            try:
                config_dict["voice_id"] = get_env_value(env_vars, "eleven_labs_voice_id", "ELEVEN_LABS_VOICE_ID")
            except:
                config_dict["voice_id"] = "9BWtsMINqrJLrRacOk9x"  # Default voice
        
        config_dict.setdefault("optimize_streaming_latency", 1)
        config_dict.setdefault("experimental_streaming", False)
        config_dict.setdefault("stability", 0.75)
        config_dict.setdefault("similarity_boost", 0.75)
        config_dict.setdefault("model_id", "eleven_flash_v2_5")
        config_dict.setdefault("experimental_websocket", False)
        config_dict.setdefault("backchannel_amplitude_factor", 0.5)
        
    elif synthesizer_config.type == "azure":
        config_dict["speech_key"] = get_env_value(env_vars, "azure_speech_key", "AZURE_SPEECH_KEY")
        config_dict["speech_region"] = get_env_value(env_vars, "azure_speech_region", "AZURE_SPEECH_REGION")
        config_dict.setdefault("voice_name", "en-US-SteffanNeural")
        config_dict.setdefault("pitch", 0)
        config_dict.setdefault("rate", 15)
        config_dict.setdefault("language_code", "en-US")
        
    elif synthesizer_config.type == "play_ht":
        config_dict["api_key"] = get_env_value(env_vars, "play_ht_api_key", "PLAY_HT_API_KEY")
        config_dict["user_id"] = get_env_value(env_vars, "play_ht_user_id", "PLAY_HT_USER_ID")
        
    elif synthesizer_config.type == "rime":
        config_dict["api_key"] = get_env_value(env_vars, "rime_api_key", "RIME_API_KEY")
        
    elif synthesizer_config.type == "cartesia":
        config_dict["api_key"] = get_env_value(env_vars, "cartesia_api_key", "CARTESIA_API_KEY")
        
    elif synthesizer_config.type == "polly":
        config_dict["aws_access_key_id"] = get_env_value(env_vars, "aws_access_key_id", "AWS_ACCESS_KEY_ID")
        config_dict["aws_secret_access_key"] = get_env_value(env_vars, "aws_secret_access_key", "AWS_SECRET_ACCESS_KEY")
        config_dict.setdefault("region_name", get_env_value(env_vars, "aws_region", "AWS_REGION"))
    
    return synthesizer_class(**config_dict)

def create_telephony_config(telephony_config: Optional[TelephonyConfiguration], env_vars: Optional[EnvironmentVariables]):
    """Create telephony configuration"""
    if not telephony_config:
        telephony_config = TelephonyConfiguration(
            type="twilio",
            config={}
        )
    
    if telephony_config.type == "twilio":
        config_dict = telephony_config.config.copy()
        config_dict["account_sid"] = get_env_value(env_vars, "twilio_account_sid", "TWILIO_ACCOUNT_SID")
        config_dict["auth_token"] = get_env_value(env_vars, "twilio_auth_token", "TWILIO_AUTH_TOKEN")
        return TwilioConfig(**config_dict)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported telephony type: {telephony_config.type}")

class CallRequest(BaseModel):
    # Required fields
    to_phone: str
    
    # Optional environment variables override
    env_vars: Optional[EnvironmentVariables] = None
    
    # Service configurations (with sensible defaults)
    agent: Optional[AgentConfiguration] = None
    transcriber: Optional[TranscriberConfiguration] = None
    synthesizer: Optional[SynthesizerConfiguration] = None
    telephony: Optional[TelephonyConfiguration] = None
    
    # Call-specific settings
    base_url: Optional[str] = None
    from_phone: Optional[str] = None
    prompt_preamble: Optional[str] = None
    initial_message: Optional[str] = None

    webhooks: Optional[List[str]] = None  # List of webhook URLs for call events

@app.post("/start_call")
async def start_call(request: CallRequest):
    """Starts a configurable call to the given phone number.

    Args:
        request (CallRequest): A request body containing all call configuration.

    Returns:
        dict: A message indicating that the call has been started.
    """
    try:
        # Use provided base_url or fall back to global BASE_URL
        call_base_url = request.base_url or BASE_URL
        
        # Get from_phone from env_vars, request, or system environment
        from_phone = request.from_phone
        if not from_phone:
            from_phone = get_env_value(request.env_vars, "twilio_phone_number", "TWILIO_PHONE_NUMBER")
        
        # Create configurations using helper functions
        agent_config = create_agent_config(
            request.agent, 
            request.prompt_preamble, 
            request.initial_message, 
            request.env_vars
        )
        
        transcriber_config = create_transcriber_config(
            request.transcriber, 
            request.env_vars
        )
        
        synthesizer_config = create_synthesizer_config(
            request.synthesizer, 
            request.env_vars
        )
        
        telephony_config = create_telephony_config(
            request.telephony, 
            request.env_vars
        )
        
        # Create and start the outbound call
        outbound_call = OutboundCall(
            base_url=call_base_url,
            to_phone=request.to_phone,
            from_phone=from_phone,
            config_manager=config_manager,
            agent_config=agent_config,
            telephony_config=telephony_config,
            transcriber_config=transcriber_config,
            synthesizer_config=synthesizer_config,
            webhooks=request.webhooks or [],
        )
        
        response = await outbound_call.start()
        logger.info(f"Call started to {request.to_phone} with custom configuration")
        
        return {
            "message": f"Call started to {request.to_phone}",
            "configuration": {
                "agent_type": request.agent.type if request.agent else "chatgpt",
                "transcriber_type": request.transcriber.type if request.transcriber else "deepgram",
                "synthesizer_type": request.synthesizer.type if request.synthesizer else "eleven_labs",
                "telephony_type": request.telephony.type if request.telephony else "twilio"
            },
            "execution_id": response.get("conversation_id"),
            "telephony_id": response.get("telephony_id"),
            "to_phone": request.to_phone,
            "from_phone": from_phone,
            "webhooks": request.webhooks or []
        }
        
    except Exception as e:
        logger.error(f"Error starting call: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start call: {str(e)}")

@app.get("/supported_services")
async def get_supported_services():
    """Get list of all supported service types"""
    return {
        "agents": list(AGENT_CONFIG_MAP.keys()),
        "transcribers": list(TRANSCRIBER_CONFIG_MAP.keys()),
        "synthesizers": list(SYNTHESIZER_CONFIG_MAP.keys()),
        "telephony": ["twilio"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
