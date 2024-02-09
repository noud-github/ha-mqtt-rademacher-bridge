################################################################################
# MQTT message translator
# This script is used to pass messages between homepilot (start2smart) and home assistant
#-------------------------------------------------------------------------------
# inspired by https://github.com/amayii0/Homie-PiDome-MQTT-translator
################################################################################



################################################################################
# Settings
verbose = False
mqtt_server = "mqttpi.lan"
mqtt_port = 1883

TRANSACTION_ID_START = 10000
MAX_TRANSACTION_ID = 99999999
TransID = TRANSACTION_ID_START

commands = {
    "STOP":  "01070200000000000000000000",
    "OPEN":  "01070100000000000000000000",
    "CLOSE": "01070300000000000000000000"
}





topicPrefixHomepilot = "homepilot/"
topicPrefixHomeAssistant = "homeassistant/"

topics = {
  topicPrefixHomepilot + "DFStickService/event",
  topicPrefixHomeAssistant + "cover/#"
}



################################################################################
# Import packages
import sys
import paho.mqtt.client as mqtt
import os
import re
import json
import random


################################################################################
# Actual translation logic
def mapCommand(cmd):
  return getFromDic(commands, cmd, "")

def translateTopicFromHomepilotToHomeAssistant(mqttc, msg):
  msgpayloadjson = json.loads(msg.payload)
  sender = msgpayloadjson["payload"]["sender"]
  command = msgpayloadjson["payload"]["command"]
  received_data = msgpayloadjson["payload"]["received_data"]
  # print (received_data)
  # print (msg.retain)
  
  # print (msg.topic)
  if msg.topic == "homepilot/DFStickService/event":
    if command == "0f23":
      pos = int(received_data[14:14 + 2], 16) & 0x7F
    
      timerAuto = "on" if int(received_data[6:6 + 2], 16) & 0x01 else "off"
      block = "1" if int(received_data[4:4 + 2], 16) & 0x40 else "0"
    elif command == "0f21":
      print (received_data[14:14 + 2])
      pos = int(received_data[14:14 + 2], 16) & 0x7F
      timerAuto = "on" if int(received_data[6:6 + 2], 16) & 0x01 else "off"
      block = "1" if int(received_data[4:4 + 2], 16) & 0x40 else "0"
    else:
      return ""
  else:
    return ""
  msg.retain = 1
  pos = pos if 0 <= pos <= 100 else 50
  msg.payload = "{\"pos\": \"" + str(100 - pos) + "\", \"timerauto\": \"" + timerAuto + "\", \"block\": \"" + block + "\"}" 
  return topicPrefixHomeAssistant + "cover/" + sender + "/state"

def translateTopicFromHomeAssistantToHomepilot(mqttc, msg):
  topicParts = re.split('/', msg.topic)
  payload = ""
  cmd = msg.payload.decode()
  if len(topicParts) > 3:
    if topicParts[1] == "cover": 
      deviceID = topicParts[2]
      print(">    " + TranslateSend_data(cmd))
      if any( [topicParts[3] == "set", topicParts[3] == "setpos" ]):
        payload = "{\"request_type\":\"MESSAGESEND\",\"transaction_id\":" + str(getActualTransactionID()) + ",\"service_name\":\"HomeAssistant\",\"payload\":{\"destination\":\"" + deviceID + "\",\"send_data\":\"" + TranslateSend_data(cmd) + "\",\"send_type\":0}}"
      
  if payload != "":
    msg.retain = 0
    msg.payload = payload
    return "homepilot/DFStickService/request"
  else:
    return "" 
 
def translateTopic(mqttc, msg):
  # Let's dump some details
  if verbose:
    print("Translating message")
    print("  > TOPIC  : " + str(msg.topic))
    print("  > QOS    : " + str(msg.qos))
    print("  > PAYLOAD: " + str(msg.payload))

  # Check if we need to translate a topic received from Homie or PiDome
  res = ""      
  if msg.topic.startswith(topicPrefixHomepilot):
    res = translateTopicFromHomepilotToHomeAssistant(mqttc, msg)
  if msg.topic.startswith(topicPrefixHomeAssistant):
    res = translateTopicFromHomeAssistantToHomepilot(mqttc, msg)

  return res

def getActualTransactionID():
    global TransID
    '''
    Returns a new calculated transaction identifier
    '''
    TransID = TransID + 1
    if (TransID) > MAX_TRANSACTION_ID:
        TransID = TRANSACTION_ID_START
    return TransID

def TranslateSend_data(msg):
    if RepresentsInt(msg):
      value = str(hex(100 - int(msg))[2:4].zfill(2))
      return "01070700" + value + "0000000000000000"
    else:
      return mapCommand(msg)
    

################################################################################
# Utilities functions
def cls():
    os.system('cls' if os.name=='nt' else 'clear')
    
    
def dumpTopicParts(parts, printPrefix):
  if verbose:
    for idx, val in enumerate(parts):
      print(str(printPrefix) + "[" + str(idx) + "] " + str(val))
      
      
def getFromDic(dic, key, default):
  if key in dic:
    return dic[key]
  else:
    if verbose:
      print("Unknown key:" + str(key))
    return default # Not found

def RepresentsInt(s):
    try: 
        int(s)
        return True
    except ValueError:
        return False


################################################################################
# Event handlers
def on_connect(mqttc, obj, flags, rc):
  print("rc: " + str(rc))


def on_message(mqttc, userdata, msg):
  print(msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
  translatedTopic = translateTopic(mqttc, msg)
  if verbose:
    print("Translated topic: " + str(translatedTopic))
    
  if translatedTopic == "":
    if verbose:
      print("Not able to translate this topic : " + msg.topic)
  else:
    # http://www.hivemq.com/blog/mqtt-essentials-part-6-mqtt-quality-of-service-levels
    iQoS = 0 # Enforce only once
    # https://eclipse.org/paho/clients/python/docs/#publishing
    #bRetain = bool(msg.retain)
    bRetain = bool(msg.retain)
    print("  > Publishing translated topic : " + translatedTopic + ", QoS=" + str(iQoS) + ", Payload=" + str(msg.payload) + ", Retain= " + str(bRetain))
    mqttc.publish(translatedTopic, msg.payload, iQoS, bRetain)


def on_publish(mqttc, obj, mid):
  print("mid: " + str(mid))


def on_subscribe(mqttc, obj, mid, granted_qos):
  print("Subscribed: " + str(mid) + " " + str(granted_qos))


def on_log(mqttc, obj, level, string):
  print(string)



################################################################################
# Subscribe to topics we want to translate
# Note that in the case of a SETTER from PiDome to HomieNode, we won't translate the HomieNode topic again
def subscribeToTopics(mqttc):
  for val in topics:
    print("Subscribing to topic : " + val)
    mqttc.subscribe(val, 0)



################################################################################
# Actual main process
# It will listen forever, translate received messages and publish them back
def mainProcess():
  # Clean screen
  cls()

  # Setup MQTT client  
  mqttc = mqtt.Client()
  mqttc.on_connect = on_connect
  mqttc.on_message = on_message # Required!
  #mqttc.on_publish = on_publish
  mqttc.on_subscribe = on_subscribe
  #mqttc.on_log = on_log # For debug only
  
  # Let's do our "magic"
  mqttc.connect(mqtt_server, mqtt_port, 60)
  subscribeToTopics(mqttc)
  mqttc.loop_forever() # Really; we don't want to leave


# Run it
mainProcess()
