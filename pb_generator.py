import json
from constant import *


class JsonPb:
    def __init__(self, json_obj, version, file):
        self.json_obj = json_obj
        self.protobuff = ''
        self.protobuff_version = version
        self.file = file

    def parse_json_to_pb(self):
        """
        main function that parse all json to pb
        """
        if self.protobuff_version == 3:
            self.protobuff = 'syntax = "proto3" \n'
        else:
            self.protobuff = ''

        for key in self.json_obj:

            if type(self.json_obj[key]) is dict and key not in [GRPC, OPTIONS, OPTIONS_EXTEND]:
                message_name = f"message {key.capitalize()} \n" + "{ \n"
                self.protobuff += self.parse_message(key, self.json_obj[key], message_name)

            elif key == SERVICE:
                message_name = f"service {self.json_obj[key].capitalize()} \n" + "{ \n"
                self.protobuff += self.parse_grpc(self.json_obj["grpc"], message_name)

            elif key == OPTIONS:
                message_name = ""
                self.protobuff += self.parse_options(self.json_obj[key], message_name)

            elif key == OPTIONS_EXTEND:
                message_name = ""
                self.protobuff += self.parse_options_extend(self.json_obj[key], message_name)

            elif key == IMPORT:
                message_name = f"import {self.json_obj[key]} \n\n"
                self.protobuff += message_name

        self.write_protobuff()

        return self.protobuff

    def parse_message(self, key, message_dict, message_name):
        """
        :return: message dict

        parse message from json to protobuff
        """
        count = 0

        message = ""
        for types in message_dict:
            if type(message_dict) is dict and not message_dict[types].get(TIMES) \
                    and not message_dict[types].get(FIELDS) and types != OPTIONS:
                message_name += f"message {types.capitalize()} \n" + "{ \n"
                message_name += self.parse_message(key, message_dict[types], "")
                message = ""
                continue

            elif message_dict[types].get(TYPE) == ENUM:
                message_name += self.parse_enum(key, types)
                message = ""
                continue

            elif types == "options":
                message_name = self.parse_options(message_dict[types], message_name)
                message = ""
                continue

            s = message_dict[types][TIMES]
            count += 1
            s += f" {message_dict[types][TYPE]} {types} = {count}"

            if message_dict[types].get(DEFAULT):
                s += f" [default = {message_dict[types][DEFAULT]}]"

            if message_dict[types].get(OPTIONS):
                for k, v in message_dict[types][OPTIONS].items():
                    s += f" [{k} = {v}]"

            s += ";\n"
            message += s
            message_name += f"{message}"
            message = ""
        message_name += "}\n\n"
        return message_name

    def parse_enum(self, key, types):
        """
        parse enum only from json to protobuff
        """
        message_name = ""
        s = f"enum {types.capitalize()} \n"
        s += "{ \n"
        enum_count = 0

        for field in self.json_obj[key][types][FIELDS]:
            s += f"{field}= {enum_count};\n"
            enum_count += 1

        if type(self.json_obj[key][types][OPTIONS]) is dict:
            s = self.parse_options(self.json_obj[key][types][OPTIONS], s)

        s += "}\n"
        message_name += s
        return message_name

    def parse_grpc(self, message_dict, message_name):
        """
        parse grpc service only from json to protobuff
        """
        message = ""
        for types in message_dict:

            if types == OPTIONS:
                message = self.parse_options(message_dict[types], message)
            else:
                message += f"rpc {types} ({message_dict[types][ARG]}) returns"

                if message_dict[types][RETURNS]:
                    message += f" ({message_dict[types][RETURNS]}) "
                else:
                    message += " (Empty) "

                message += "{ "
                if message_dict[types].get(OPTIONS):
                    message = self.parse_options(message_dict[types][OPTIONS], message)

                message += "}\n"

            message_name += f"{message}"
            message = ""
        message_name += "}\n\n"
        return message_name

    def parse_options(self, message_dict, message_name):
        for option in message_dict:
            if option.find(".") != -1:
                option_method = option.split(".")
                message_name += f"option ({option_method[0]}).{option_method[1]} = '{message_dict[option]}' ;\n"
            else:
                message_name += f"option ({option}) = '{message_dict[option]}';\n"
        return message_name

    def parse_options_extend(self, message_dict, message_name):
        for extend in message_dict:
            message = f"extend {extend} "
            message += "{ \n"
            message += f"{message_dict[extend][TIMES]} {message_dict[extend][TYPE]} {message_dict[extend][KEY]} " \
                       f"= {message_dict[extend][VALUE]};\n "
            message += "}\n"
            message_name += message

        return message_name

    def write_protobuff(self):
        """
        write protobuff parser in the file
        """
        with open(f"{self.file}.proto", "w") as file:
            file.write(self.protobuff)


f = open('pb.json')
data = json.loads(f.read())

z = JsonPb(data, 3, "proto_generator")
print(z.parse_json_to_pb())
f.close()
