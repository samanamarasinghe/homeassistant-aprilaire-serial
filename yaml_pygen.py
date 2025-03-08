import os
import yaml
import json

# This is for modbus Generation
sensor_map = {
    (3,1):"Unknown_3_1",
    (3,2):"Unknown_3_2",
    (3,3):"Unknown_3_3",
    (3,4):"Unknown_3_4",
    (3,5):"Unknown_3_5",
    (3,6):"Unknown_3_6",
    (3,7):"Unknown_3_7",
    (3,8):"Unknown_3_8",
    (3,9):"Unknown_3_9",
    (3,10):"Unknown_3_10",
    (3,11):"Unknown_3_11",
    (3,12):"Unknown_3_12",
    (3,13):"Unknown_3_13",
    (3,14):"Unknown_3_14",
    (3,15):"Unknown_3_15",
    (3,16):"Unknown_3_16",
    (3,17):"Unknown_3_17",
    (3,18):"Unknown_3_18",
    (3,19):"Unknown_3_19",
    (3,20):"Unknown_3_20",
    (3,21):"Unknown_3_21",
    (3,22):"Unknown_3_22",
    (3,23):"Unknown_3_23",
    (3,24):"Unknown_3_24",
    (3,25):"Unknown_3_25",
    (3,26):"Unknown_3_26",
    (3,27):"Unknown_3_27",
    (3,28):"Unknown_3_28",
    (3,29):"Unknown_3_29",
    (3,30):"Unknown_3_30",
    (3,31):"Unknown_3_31",
    (3,32):"Unknown_3_32",
    (3,33):"Unknown_3_33",
    (3,34):"Unknown_3_34",
    (3,35):"Unknown_3_35",
    (3,36):"Unknown_3_36",
    (3,37):"Unknown_3_37",
    (3,38):"Unknown_3_38",
    (3,39):"Unknown_3_39",
    (3,40):"Unknown_3_40",
    (3,41):"Unknown_3_41",
    (3,42):"Unknown_3_42",
    (2,1):'Master Study Plugs',
    (2,2):"Amma Suite Outlets",
    (2,3):"Master Study Panel 1",
    (2,4):"Kitchen  trash + cooktop+dishwasher",
    (2,5):"Master Study Panel 2",
    (2,6):"Kitchen lights",
    (2,7):"Fridge",
    (2,8):"Unknown_2_8",
    (2,9):"Freezer",
    (2,10):"Guest and Bath lights",
    (2,11):"Guest Bath GFCI",
    (2,12):"Seth Lights and power",
    (2,13):"Kitchen/Amma Air Handler",
    (2,14):"Attic Plug",
    (2,15):"2nd floor corridor putlets",
    (2,16):"Amma + corridor lights",
    (2,17):"Master Bath Light",
    (2,18):"Closet Lights",
    (2,19):"Stairwell lights",
    (2,20):"Small closet (chandelier)/Basement lights",
    (2,21):"Master. Bedroom outlets",
    (2,22):"Library. Light",
    (2,23):"Living Air Handler",
    (2,24):"Wine Cooler",
    (2,25):"Heating",
    (2,26):"Dining Outlet",
    (2,27):"Garage Door",
    (2,28):"bigred_2_28",
    (2,29):"Unknown_2_29",
    (2,30):"bigred_2_30",
    (2,31):"Unknown_2_31",
    (2,32):"Washer/Driyer Power",
    (2,33):"Unknown_2_33",
    (2,34):"Unknown_2_34",
    (2,35):"Basement Lights",
    (2,36):"Unknown_2_36",
    (2,37):"Unknown_2_37",
    (2,38):"Unknown_2_38",
    (2,39):"Elevator",
    (2,40):"Rack Power 1",
    (2,41):"Microwave / Elevator",
    (2,42):"Rack Power 2", 
}

sensor_file = "/config/pygen_sensors.yaml"
template_file = "/config/pygen_templates.yaml"
integration_file = "/config/pygen_integration.yaml"

# sensor_config = [
#     {
#         "type": "tcp",
#         "host": "192.168.3.153",
#         "port": 502,
#         "name": "power_meter",
#         "sensors": [
#         ]
#     }
# ]


# Modbus Sensors
sensor_config = [
    {
        "type": "serial",
        "method": "rtu",
        "port": "/dev/ttyUSB1",
        "baudrate": 9600,
        "stopbits": 1,
        "bytesize": 8,
        "parity": "N",
        "name": "Veris_Brnach_Current_Meter",
        "sensors": [
        ]
    }
]


slaves = [2, 3]
addresses = [i for i in range(1,43)]


# Generate all Modbus sensors
for s in slaves:
    for a in addresses:
        sensor_config[0]["sensors"].append({
            "name": f"veris_current_meter_{s}_{a}",
            "slave": s,
            "address": a,
            "input_type": "holding",
            "unit_of_measurement": "mA",
            "scale": 1,
            "precision": 0,
            "device_class": "current",
            "state_class": "measurement",
        })

# Dump the YAML file with correct formatting
with open(sensor_file, "w") as f:
    yaml.dump(sensor_config, f, default_flow_style=False, sort_keys=False)

# Define the base Template sensor structure
template_config = [
    {
        "sensor": [ 
        ]
    }
]

# Generate Kaha Sulaga Sensor
template_config[0]["sensor"].append({
    "name": "`Forecast KahaSulaga Temperature`",
    "unique_id": "orecast_kahasulaga_temp",
    "state": "{{{{ states_attr(\"weather.forecast_kahasulaga\", \"temperature\") }}}}",
    "unit_of_measurement": "F",
    "device_class": "temprature",
})

# Tekmar sensors
for t in [1001, 1002, 1003, 1004, 1005]:
    template_config[0]["sensor"].append({
        "name": f"`Tekmar {str(t)} Action`",
        "unique_id": f"tekmar_{str(t)}_action",
        "device_class" : "enum",
        "state" : f"{{{{ state_attr(\"climate.tekmarnet_thermostat_542_{str(t)}\", \"hvac_action\")  }}}}",
        "attributes": {
            "setpoint": f"{{{{ state_attr(\"climate.tekmarnet_thermostat_542_{str(t)}\", \"temprature\")  }}}}",
        },
    })          

# Generate all template sensors for modbus
for s in slaves:
    for a in addresses:
        template_config[0]["sensor"].append({
            "name": f"`{sensor_map[(s, a)]}`",
            "unique_id": f"power_meter_{s}_{a}_extended",
            "state": f"{{{{ states(\"sensor.veris_current_meter_{s}_{a}\")| float(0) * state_attr(\"sensor.power_meter_{s}_{a}_extended\", \"voltage\") | float(110) / 10000.0 }}}}",
            "unit_of_measurement": "W",
            "device_class": "power",
            "state_class": "measurement",
            "attributes": {
                "voltage": f"{{{{ 110 | float }}}}",
            }
        })
# Dump the YAML file with correct formatting
with open(template_file, "w") as f:
    yaml.dump(template_config, f, default_flow_style=False, sort_keys=False)


integration_config = [ ]

for s in slaves:
    for a in addresses:
        integration_config.append({
            "platform": "integration",
            "name": f"`{sensor_map[(s, a)]} Energy`",
            "unique_id": f"power_meter_{s}_{a}_energy",
            "source": f"sensor.power_meter_{s}_{a}_extended",
#            "state": """ >
#        {% set value = states('sensor.power_meter') %}
#        {% if value not in ['unknown', 'unavailable', 'None'] %}
#            {{ value | float(0) }}
#        {% else %}
#            0
#        {% endif %}
#        """,
            "unit_prefix": "k",
            "round": "3",
            "method": "trapezoidal",
#            "default": "0",
        })    

# Dump the YAML file with correct formatting
with open(integration_file, "w") as f:
    yaml.dump(integration_config, f, default_flow_style=False, sort_keys=False)



print(f"✅ Modbus YAML generated successfully at: {sensor_file} and {template_file} and {integration_file}")

