import can
import time
import threading

## ID Groups
SINGLE_MOTOR = 0x140
MULTI_MOTOR = 0x280
CAN_SETTING = 0x300

## Commands
CANID_SETTING_CMD = 0x79
FUNCTION_CONTROL_CMD = 0x20
READ_MOTOR_STATUS_1_CMD = 0x9A
MOTOR_SHUTDOWN_CMD = 0x80

## Flags
CAN_ID_WRITE_FLAG = 0x00
CAN_ID_READ_FLAG = 0x01
REPLY_COMMAND = 0x240

## Function Index
CANID_FILTER_ENABLE = 0x02

BITRATE = 1000000
# BITRATE = 500000

def receive_can_messages():
    with can.interface.Bus(channel='can0', bustype='socketcan', bitrate=BITRATE) as bus:
        msg = bus.recv()
        if msg is not None:
            print(f"Get message: {msg}")

def send_can_command(arbitration_id, data_predefined):
    """Sends a single message."""
    with can.interface.Bus(channel='can0', bustype='socketcan', bitrate=BITRATE) as bus:
        msg = can.Message(
            arbitration_id=arbitration_id,
            data=data_predefined,
            is_extended_id=False
        )

        try:
            bus.send(msg)
            print(f"Message sent on {bus.channel_info}")

            reply = bus.recv(timeout=0.5)
            return reply

        except can.CanError:
            print("Message NOT sent")
            return None

def set_canid_filter(enable):
    data_to_set_filter = [FUNCTION_CONTROL_CMD, CANID_FILTER_ENABLE, 0x00, 0x00, enable, 0x00, 0x00, 0x00]
    reply = send_can_command(SINGLE_MOTOR+current_id, data_to_set_filter)
    if reply is not None and reply.arbitration_id == current_id+REPLY_COMMAND:
        data = reply.data
        if data[0] == FUNCTION_CONTROL_CMD and data[1] == CANID_FILTER_ENABLE and data[4] == enable:
            print(f"CANID filter {'enabled' if enable else 'disabled'} successfully")
        else:
            print(f"Failed to {'enable' if enable else 'disable'} CANID filter")
    else:
        print("No reply or invalid reply received")

def shutdown_motor():
    data_to_shutdown = [MOTOR_SHUTDOWN_CMD, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
    reply = send_can_command(SINGLE_MOTOR+current_id, data_to_shutdown)
    if reply is not None and reply.arbitration_id == current_id+REPLY_COMMAND:
        data = reply.data
        if data[0] == MOTOR_SHUTDOWN_CMD:
            print("Motor shutdown successfully (New Setting Applied)")
        else:
            print("Failed to shutdown motor")
    else:
        print("No reply or invalid reply received")

if __name__ == "__main__":
    current_id = None

    # Search for a motor ID using 0x9A command
    for motor_id in range(1, 33):
        print(f"Scanning motor with ID {motor_id}: ")                
        data_to_read_status = [READ_MOTOR_STATUS_1_CMD, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        reply = send_can_command(SINGLE_MOTOR+motor_id, data_to_read_status)
        if reply is not None and reply.arbitration_id == motor_id+REPLY_COMMAND:
            current_id = motor_id
            print("")
            print(f"Found a motor with ID {current_id}")
            break

    if current_id is None:
        print("No motor found")
    else:
        # Ask user to enable or disable CANID filter
        while True:
            print("")            
            print("If you want to proceed for CAN id settings, CANID_filter setting will be disabled.")
            user_input = input("Do you want to chanage CAN ID Settings? (y/n): ")
            if user_input.lower() == 'n':
                break
            elif user_input.lower() == 'y':
                set_canid_filter(0x00)
                time.sleep(1)                                 
                print("Shutdown motor and wait for 2 seconds")                            
                shutdown_motor()
                time.sleep(2)                 
                break
            else:
                print("Invalid input. Please enter 'y' or 'n'.")

        if user_input.lower() == 'y':
            # Ask user if they want to change the motor ID
            while True:
                print("")                            
                user_input = input("Do you want to change the motor ID? (y/n): ")
                if user_input.lower() == 'y':
                    # Get new Motor ID from user
                    while True:
                        try:
                            new_id = int(input("Enter a new Motor ID (1-32): "))
                            if 1 <= new_id <= 32:
                                break
                            else:
                                print("Motor ID must be in the range of 1 to 32")
                        except ValueError:
                            print("Invalid input. Please enter a number.")

                    # Set new Motor ID
                    data_to_write_id = [CANID_SETTING_CMD, 0x00, CAN_ID_WRITE_FLAG, 0x00, 0x00, 0x00, 0x00, new_id] # new_id can be treated as int, too
                    reply = send_can_command(CAN_SETTING, data_to_write_id)
                    if reply is not None and reply.arbitration_id == CAN_SETTING: # Flag is not REPLY_COMMAND in this case
                        data = reply.data
                        if data[0] == CANID_SETTING_CMD and data[2] == CAN_ID_WRITE_FLAG and data[7] == new_id:
                            print(f"Motor ID {new_id} set successfully")
                            current_id = new_id
                            # Shutdown motor and wait for 2 seconds
                            time.sleep(1)                                                        
                            print("Shutdown motor and wait for 2 seconds")                            
                            shutdown_motor()
                            time.sleep(2)                            
                        else:
                            print(f"Failed to set Motor ID {new_id}")
                    else:
                        print("No reply or invalid reply received")
                    break
                elif user_input.lower() == 'n':
                    print("Skipping Motor ID setting")
                    break
                else:
                    print("Invalid input. Please enter 'y' or 'n'.")

        # Ask user to enable or disable CANID filter after ID change
        while True:
            print("!!")  
            print("PLEASE SHUTDOWN AND RESTART MOTOR FROM POWER SUPPLY **MANUALLY**.")
            print("!!")  
            print("And determine if you eanble or diable CANID filter setting:")                                              
            print("Enabling CANID filter will improve the efficiency of motor sending and receiving in CAN communication.")
            print("Disabling CANID filter is necessary when using the multi-motor control command 0x280.")
            user_input = input("Do you want to enable CANID filter? (y/n): ")
            if user_input.lower() == 'y':
                set_canid_filter(0x01)
                time.sleep(1)                                    
                print("Shutdown motor and wait for 2 seconds")
                shutdown_motor() 
                time.sleep(2)                    
                break
            elif user_input.lower() == 'n':
                set_canid_filter(0x00)
                time.sleep(1)                    
                print("Shutdown motor and wait for 2 seconds")                
                shutdown_motor()                
                time.sleep(2)                    
                break
            else:
                print("Invalid input. Please enter 'y' or 'n'.")

        print("")
        print(f"Motor configuration completed. Current ID: {current_id}, CANID filter: {'enabled' if user_input.lower() == 'y' else 'disabled'}")