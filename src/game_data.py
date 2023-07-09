# game_data.py


# Может еще пригодится. Пока оставлю.
# class GameData:
#
#     def __get_game_version(self) -> str:
#         """Возвращает строку с последней версией игры"""
#         try:
#             comlink_request = requests.post(f"{API_LINK}/metadata")
#             comlink_request.raise_for_status()
#             data = comlink_request.json()
#             return data['latestGamedataVersion']
#         except requests.exceptions.HTTPError:
#             raise Status404Error("There was an error getting comlink metadata.")
#
#     def get_game_data(self) -> dict:
#         """Формирует словарь с данными из игры (только нужные)"""
#         version: str = self.__get_game_version()
#         post_data = {
#             "payload": {
#                 "version": version,
#                 "includePveUnits": True,
#                 "requestSegment": 2
#             },
#             "enums": False
#         }
#         result = {}
#         try:
#             comlink_request = requests.post(f"{API_LINK}/data", json=post_data)
#             comlink_request.raise_for_status()
#             data = comlink_request.json()
#             print(data.keys())
#             for i in data['statModSet']:
#                 print(i)
#         except requests.exceptions.HTTPError:
#             raise Status404Error("There was an error getting comlink metadata.")
#         return result
