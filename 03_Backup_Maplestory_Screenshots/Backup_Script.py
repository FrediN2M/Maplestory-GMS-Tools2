import os
import shutil
import json
from loguru import logger


# Define function to move files
def move_files(source_path, destination_path):
    total_files = 0
    total_size = 0

    try:
        # Check if the destination path exists, create if it doesn't
        if not os.path.exists(destination_path):
            os.makedirs(destination_path)

        # Iterate through files in the source directory
        for file_name in os.listdir(source_path):
            if file_name.startswith("Maple") and file_name.endswith(".jpg"):
                source_file = os.path.join(source_path, file_name)

                # Prepare the destination file path
                destination_file = os.path.join(destination_path, file_name)

                # Check if the destination file already exists
                if os.path.exists(destination_file):
                    base_name, extension = os.path.splitext(file_name)
                    counter = 1
                    # Create a new filename with a suffix until it doesn't exist
                    while os.path.exists(destination_file):
                        destination_file = os.path.join(destination_path, f"{base_name}({counter}){extension}")
                        counter += 1

                # Move the file
                shutil.move(source_file, destination_file)
                file_size = os.path.getsize(destination_file)
                total_size += file_size
                total_files += 1

                logger.info(f"Moved {file_name} to {destination_file} ({file_size / 1024:.2f} KB)")

    except Exception as e:
        logger.error(f"Error while moving files: {e}")

    # Log total number of files and total size moved
    logger.info(f"Total files moved: {total_files}")
    logger.info(f"Total size moved: {total_size / (1024 * 1024):.2f} MB")


def load_config():
    try:
        with open('config.json') as json_file:
            return json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading config: {e}")
        raise


if __name__ == '__main__':
    logger.add("App_Log_{time}.log", rotation="30 days", backtrace=True, enqueue=False, catch=True)
    # Load configuration from config.json
    config = load_config()

    destination_path = config["destination_path"]
    use_steam = config["use_steam"]
    use_nexon = config["use_nexon"]

    # Determine which client to use based on the flag
    if use_steam == 1:
        steam_game_path = config["steam_game_path"]
        logger.info("Using Steam game path")
        move_files(steam_game_path, destination_path)
    elif use_nexon == 1:
        nexon_game_path = config["nexon_game_path"]
        logger.info("Using Nexon game path")
        move_files(nexon_game_path, destination_path)
    else:
        logger.warning("No valid game client selected")
