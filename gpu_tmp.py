import requests
import subprocess 
from datetime import datetime
from platform import node
import socket
import logging
from time import sleep
import pytz 

CONNECTION_ADDRESS = "8.8.8.8"
CONNECTION_CHECK_TIMEOUT = 5
SHUTDOWN_COMMAND = "shutdown -h now"
RETRY = 10
INTERVAL = "50s"
WEBHOOK_URL = "<YOUR WEB_HOOK>"
LOG_PATH = "service.log"
THRESHOLD = 10

logging.basicConfig(
    filename=LOG_PATH,              
    filemode="a",                    
    level=logging.INFO,              
    format="%(asctime)s [%(levelname)s]: %(message)s"
)

logger = logging.getLogger()

def check_internet() -> bool:
    try:
        socket.create_connection((CONNECTION_ADDRESS, 53), timeout=CONNECTION_CHECK_TIMEOUT)
        return True
    except OSError:
        logger.warning(f"Connection refused. ({CONNECTION_ADDRESS})")
        return False

def get_gpus_temp() -> str | None:

    try:
        result = subprocess.run(
            ["bash", "./script.sh"],
            capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
      values = {"server_name":get_node_name(), "message": "nvidia-smi command not found.", "timestamp":get_now_data_time("%Y-%m-%d %H:%M:%S %Z %z")}
      logger.error("nvidia-smi command not found.")
      call_rocketchat_webhook(webhook_url=WEBHOOK_URL,temp_name="fail",**values)
      return None
       
def fill_placeholders(obj, **kwargs):
    if isinstance(obj, dict):
        return {k: fill_placeholders(v, **kwargs) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [fill_placeholders(v, **kwargs) for v in obj]
    elif isinstance(obj, str):
        try:
            return obj.format(**kwargs)
        except KeyError:
            return obj  
    else:
        return obj
    
def create_payload(template:dict,**kwargs):
  payload =fill_placeholders(
    template,
    **kwargs
)
  return payload

def call_rocketchat_webhook(webhook_url:str, temp_name="success", **kwargs):
  template:dict | None= get_template(temp_name=temp_name)
  if template is None:
    logger.error(f"{temp_name} template not found")
    raise ValueError(f"{temp_name} This template not found")
  
  payload:dict = create_payload(template=template,**kwargs)
  
  failed_connection_num = 0
  
  while True:
    if check_internet():
      response= requests.post(webhook_url, json=payload) 
      logger.info(f"{response.status_code} Message has sent to rocketchat.")
      failed_connection_num = 0
      break
    elif RETRY and RETRY > failed_connection_num:
      failed_connection_num += 1
      logger.warning(f"Connection refused. retrying ...({failed_connection_num})")
      sleep(to_seconds(INTERVAL))
    else:
      shutdown_server()
      break
      
def filter_metrics_by_threshold(threshhold:int, temp:int, gpu_model:str) -> bool:
    if temp > threshhold:
      logger.info(f"{gpu_model} temperature is above {threshhold}. (current temp is {temp})")
      return True
    else:
      logger.info(f"{gpu_model} temperature is bellow {threshhold}. (current temp is {temp})")
      return False
  
def get_gpu_info() -> dict | None:
    server_gpu_metric = get_gpus_temp()
    if server_gpu_metric:
      pure_data =  {}
      for i,metric in enumerate(server_gpu_metric.splitlines()):
        gpu_model, temp = [obj.strip() for obj in metric.split(",")]
        if filter_metrics_by_threshold(THRESHOLD,int(temp),gpu_model):
          pure_data[i] = {"server_name":get_node_name(), "gpu_model": gpu_model, "temp": temp, "timestamp":get_now_data_time("%Y-%m-%d %H:%M:%S %Z")}
      return pure_data
    else:
        logger.error("get_gpu_info couldn't get gpu info from server.")
        return None

def get_now_data_time(format:str | None):
  tehran_tz = pytz.timezone("Asia/Tehran")
  return datetime.now(tehran_tz).strftime(format) if format else datetime.now(tehran_tz)

def get_template(temp_name:str) -> dict | None:
    templates ={
    "success":{
    "text":  "🌡️GPU Temperature",
    "emoji": ":rotating_light:",               
    "attachments": [
        {
            "title": "GPU Temperature",
            "color": "#FF5733",
            "fields": [
                {"title": "Server", "value": "{server_name}", "short": True},
                {"title": "GPU Model", "value": "{gpu_model}", "short": True},
                {"title": "Temperature", "value": "{temp} °C", "short": True},
                {"title": "Time", "value": "{timestamp}", "short": True}
            ]
        }
    ]
},
    "fail":{ 
    "text":  "🌡️GPU Temperature",
    "emoji": ":rotating_light:",               
    "attachments": [
    {
      "title": "GPU Temperature",
      "color": "#FF5733",
      "fields": [
        { "title": "Server","value": "{server_name}", "short": True},
        { "title": "Server Message", "value": "{message}", "short": True},
        {"title": "Time", "value": "{timestamp}", "short": True}
        
      ]
    }
    ]
  }
    }
    template = templates.get(temp_name,None)
    return template

def shutdown_server() -> None:
  
    try:
      subprocess.run(SHUTDOWN_COMMAND.split())
    except subprocess.CalledProcessError as e:
      logger.error(f"Somethung went wrong. {e}")
      
def get_node_name() -> str:
  return node()

def to_seconds(time_str: str) -> float:
    time_str = time_str.strip().lower()
    
    if time_str.endswith("ms"):  
        return int(time_str[:-2]) / 1000
    elif time_str.endswith("s"): 
        return int(time_str[:-1])
    elif time_str.endswith("min"): 
        return int(time_str[:-3]) * 60 
    elif time_str.endswith("h"):
        return int(time_str[:-1]) * 60 * 60
    else:
        logger.error(f"Unsupported time format: {time_str}")
        raise ValueError(f"Unsupported time format: {time_str}")
 
if __name__ == "__main__":
    logger.info("Service has statrted.")
    get_gpu_metrics =  get_gpu_info()
    if get_gpu_metrics:
      for _, metric in get_gpu_metrics.items():
        call_rocketchat_webhook(webhook_url=WEBHOOK_URL,**metric)