from fast_bitrix24 import BitrixAsync
import asyncio

from Config import Config
from typing import Any, Dict, List, Optional
import datetime
import logging


class ImageService:
    @staticmethod
    def read_image_index(file_name: str) -> int:
        try:
            with open(file_name, "r") as file:
                return int(file.read())

        except (FileNotFoundError, ValueError):
            return 0

    @staticmethod
    def write_image_index(file_name: str, index: int):
        with open(file_name, "w") as file:
            file.write(str(index))


class BirthdayService:
    def __init__(self, bitrix_api: BitrixAsync, folder_id: str, bot_id: str, image_index_filename: str):
        self.bitrix_api = bitrix_api
        self.folder_id = folder_id
        self.bot_id = bot_id
        self.image_index_filename = image_index_filename

    @staticmethod
    def get_today_date() -> str:
        current_date = datetime.datetime.now()
        return '{0:02d}-{1:02d}'.format(current_date.month, current_date.day)

    async def get_employee_birthdays(self) -> List[Dict[str, Any]]:
        employees = await self.bitrix_api.get_all('user.get', {
            "FILTER": {
                "ACTIVE": "Y",
                "!PERSONAL_BIRTHDAY": ""
            },
            "SELECT": ["ID", "NAME", "LAST_NAME", "PERSONAL_BIRTHDAY", "ACTIVE"]
        })

        today_date = self.get_today_date()
        employees_birthday_today = [
            employee for employee in employees if employee.get('PERSONAL_BIRTHDAY', '')[5:10] == today_date]
        return employees_birthday_today

    @staticmethod
    def generate_conratulations_message(employee: Dict[str, Any]) -> Optional[str]:
        employee_id = employee["ID"]
        if employee_id:
            return f'[USER={employee_id}]{employee["NAME"]} {employee["LAST_NAME"]}[/USER]'
        else:
            logging.error(f"User ID not found for employee {employee['NAME']} {employee['LAST_NAME']}")
            return None

    async def get_next_image(self) -> Optional[str]:
        image_files = await self.get_all_images()
        current_index = ImageService.read_image_index(self.image_index_filename)

        if not image_files:
            return None

        next_image_id = image_files[current_index % len(image_files)]

        current_index = (current_index + 1) % len(image_files)
        ImageService.write_image_index(self.image_index_filename, current_index)

        return next_image_id

    async def get_all_images(self) -> list[Any] | None:
        response_data = await self.bitrix_api.get_all("disk.folder.getchildren", {"id": self.folder_id})
        if response_data is not None:
            return [file["ID"] for file in response_data if file["TYPE"] == "file"]

        return None

    async def get_image_public_url(self, image_id: str) -> Optional[str]:
        response = await self.bitrix_api.call("disk.file.get", {"id": image_id})
        public_url = response.get("DOWNLOAD_URL", None)

        if public_url:
            return public_url
        else:
            logging.error(f"Couldn't get the public URL for image ID: {image_id}")
            return None

    async def congratulate_employees_with_birthday(self, employees_with_birthdays):
        # Обновите эту функцию, чтобы принимать результат вызова get_employee_birthdays
        employees = employees_with_birthdays
        logging.info(f"Checking employees with birthday of {self.get_today_date()}")

        congratulations = []
        for employee in employees:
            employee_birthday = employee.get('PERSONAL_BIRTHDAY', '')[5:10]
            if self.get_today_date() in employee_birthday:
                message = self.generate_conratulations_message(employee)
                if message:
                    congratulations.append(message)

        if congratulations:
            next_image_id = await self.get_next_image()
            next_image_url = await self.get_image_public_url(next_image_id)

            params = {
                "USER_ID": self.bot_id,
                "POST_TITLE": "Поздравляем с Днём Рождения!",
                "POST_MESSAGE": f"С Днём Рождения, " + ", ".join(congratulations) + f"!\n\n[IMG]{next_image_url}[/IMG]",
                "DEST": "UA",
            }

            await self.bitrix_api.call("log.blogpost.add", params)


async def main():
    config = Config("config.json")
    config_type = "dev"
    config_data = config.read_config()

    if config_data is None:
        print("Error reading config, exiting.")
        exit()

    webhook = f"https://" \
              f"{config_data[config_type]['domain']}" \
              f"/rest/{config_data[config_type]['api_owner']}" \
              f"/{config_data[config_type]['token']}/"
    bitrix_api = BitrixAsync(webhook=webhook)

    folder_id = config_data[config_type]["folder_id"]
    bot_id = config_data[config_type]["bot_id"]
    image_index_filename = config_data[config_type]["image_index_filename"]

    birthday_service = BirthdayService(bitrix_api, folder_id, bot_id, image_index_filename)

    employees_with_birthdays = await birthday_service.get_employee_birthdays()
    await birthday_service.congratulate_employees_with_birthday(employees_with_birthdays)


if __name__ == "__main__":
    asyncio.run(main())
