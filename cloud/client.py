# cloud/client.py
from arduino_iot_cloud import ArduinoCloudClient
from secrets import DEVICE_ID, CLOUD_PASSWORD

def create_client(register_map: dict):
    """
    Create and return a configured ArduinoCloudClient.

    register_map: dict of variable_name -> kwargs for register(), e.g.:
      {
        'led_state': {'on_write': some_fn},
        'time_zh': {},
        ...
      }
    """
    client = ArduinoCloudClient(
        device_id=DEVICE_ID,
        username=DEVICE_ID,     # Arduino IoT Cloud uses deviceId as username for token auth
        password=CLOUD_PASSWORD
    )
    for var, kwargs in register_map.items():
        client.register(var, **kwargs)
    return client
