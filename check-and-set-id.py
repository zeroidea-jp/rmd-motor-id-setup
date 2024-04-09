import can
import time
import threading

## ID Groups
# SINGLE_MOTOR_COMMAND = 0x140
# MULTI_MOTOR_COMMAND = 0x280
CAN_SETTING_COMMAND = 0x300

## Commands
CANID_SETTING_CMD = 0x79

## Flags
CAN_ID_WRITE_FLAG = 0x00
CAN_ID_READ_FLAG = 0x01
REPLY_COMMAND = 0x240

BITRATE = 1000000


def receive_can_messages():
    with can.interface.Bus(channel='can0', bustype='socketcan', bitrate=BITRATE) as bus:
        msg = bus.recv()
        if msg is not None:
            print(f"Get message: {msg}")


def send_can_setting_command(data_predefined):
    """Sends a single message."""
    with can.interface.Bus(channel='can0', bustype='socketcan', bitrate=BITRATE) as bus:
        msg = can.Message(
            arbitration_id=CAN_SETTING_COMMAND,
            data=data_predefined,
            is_extended_id=False
        )

        try:
            bus.send(msg)
            print(f"Message sent on {bus.channel_info}")

            reply = bus.recv(timeout=1)
            return reply

        except can.CanError:
            print("Message NOT sent")
            return None


if __name__ == "__main__":
    # Read current Motor ID
    data_to_read_id = [CANID_SETTING_CMD, 0x00, CAN_ID_READ_FLAG, 0x00, 0x00, 0x00, 0x00, 0x00]
    reply = send_can_setting_command(data_to_read_id)
    # print("received message: ")
    # print(reply)
    if reply is not None and reply.arbitration_id == CAN_SETTING_COMMAND: # Flag is not REPLY_COMMAND in this case
        data = reply.data
        if data[0] == CANID_SETTING_CMD and data[2] == 0x01:
            current_id =  data[6] & 0x2F
            print(f"Current Motor ID is {current_id} (in integer)")                        
            current_reply_id = (data[7] << 8) | data[6]
            print(f"Current Motor reply ID is {hex(current_reply_id)}")

            # Ask user if they want to set a new ID
            while True:
                user_input = input("Do you want to set a new Motor ID? (y/n): ")
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
                    reply = send_can_setting_command(data_to_write_id)
                    if reply is not None and reply.arbitration_id == CAN_SETTING_COMMAND: # Flag is not REPLY_COMMAND in this case
                        data = reply.data
                        if data[0] == CANID_SETTING_CMD and data[2] == CAN_ID_WRITE_FLAG and data[7] == new_id:
                            print(f"Motor ID {new_id} set successfully")
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
        else:
            print("Invalid reply received")
    else:
        print("No reply or invalid reply received")