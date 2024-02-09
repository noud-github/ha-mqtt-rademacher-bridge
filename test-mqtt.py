import os
import time
from dotenv import load_dotenv
from ha_mqtt_discoverable import Settings
from ha_mqtt_discoverable.sensors import Cover, CoverInfo
from paho.mqtt.client import Client, MQTTMessage

load_dotenv()

# Configure the required parameters for the MQTT broker
mqtt_settings = Settings.MQTT(host = os.getenv('MQTT_SERVER'))

# Information about the cover
cover_info = CoverInfo(name="test" , unique_id="test1234567890")

settings = Settings(mqtt=mqtt_settings, entity=cover_info)

# To receive state commands from HA, define a callback function:
def my_callback(client: Client, user_data, message: MQTTMessage):
    payload = message.payload.decode()
    if payload == "OPEN":
	    # let HA know that the cover is opening
	    my_cover.opening()
	    # call function to open cover
        #open_my_custom_cover()
        # Let HA know that the cover was opened
	    my_cover.open()
    if payload == "CLOSE":
	    # let HA know that the cover is closing
	    my_cover.closing()
	    # call function to close the cover
        #close_my_custom_cover()
        # Let HA know that the cover was closed
	    my_cover.closed()
    if payload == "STOP":
	# call function to stop the cover
        #stop_my_custom_cover()
        # Let HA know that the cover was stopped
	    my_cover.stopped()

# Define an optional object to be passed back to the callback
user_data = "Some custom data"

# Instantiate the cover
my_cover = Cover(settings, my_callback, user_data)

# Set the initial state of the cover, which also makes it discoverable
my_cover.closed()

def main():
    while True:
        res = raw_input("Please enter search criteria, or type 'exit' to exit the program: ")
        if res=="exit":
            break
        else:
            name,val = res.split()
            if name not in friends:
                print("I don't know anyone called {}".format(name))
            elif val not in friends[name]:
                print("{} doesn't have a {}".format(name, val))
            else:
                print("{}'s {} is {}".format(name, val, friends[name][val]))

if __name__=="__main__":
    main()