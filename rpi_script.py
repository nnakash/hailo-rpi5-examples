import numpy as np
from clip_text_encoder_hef import CLIP
import re
import whisper

import re
 
# Dictionary mapping number words to digits
NUMBER_WORDS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, 
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, 
    "ten": 10
}

def replace_number_words(text):
    """
    Replace number words in a string with their numeric equivalents.
    """
    def word_to_digit(match):
        word = match.group(0).lower()
        return str(NUMBER_WORDS.get(word, word))
    # Match whole words that are in the NUMBER_WORDS dictionary
    pattern = r'\b(' + '|'.join(NUMBER_WORDS.keys()) + r')\b'
    return re.sub(pattern, word_to_digit, text)


class FeedMe:
    def __init__(self, menu_path, clip_text_encoder):
        print("Loading menu")
        menu_dict = dict(np.load(menu_path, allow_pickle=True))
        for key in menu_dict.keys():
            menu_dict[key] = menu_dict[key].item()
        self.menu = menu_dict
        self.encoder = clip_text_encoder
        self.tsh = 0.05
        return

    def split_text_to_dict(self, text):
        """
        Splits the input text by ';', extracts the number before each string,
        and returns a dictionary with the string as the key and the number as the value.

        Args:
            text (str): The input string to process.

        Returns:
            dict: A dictionary with keys as strings (excluding the leading number)
                and values as the extracted leading numbers.
        """
        result = {}
        parts = text.split(";")  # Split the text by ';'
        for part in parts:
            part = part.strip()
            # Match the format "number string"
            match = re.match(r"(\d+)\s+(.+)", part)
            if match:
                number = int(match.group(1))  # Extract the number
                key = match.group(2).strip()  # Extract the string
                result[key] = number
            else:
                raise ValueError(f"Invalid format for part: {part}")
        return result

    def parse_string_to_dict(self, input_string):
        """
        Parses a string with items and their quantities into a dictionary.

        Args:
            input_string (str): The input string, e.g., "burger ; 2 chips".

        Returns:
            dict: A dictionary with items as keys and quantities as values.
        """
        # Initialize an empty dictionary
        result = {}

        # Split the input string into parts based on delimiters (';' or spaces)
        parts = input_string.split("also")

        for part in parts:
            # Clean and split each part further based on spaces
            items = part.strip().split()

            if items:
                # Assume the last element is the quantity if it's numeric
                if items[0].isdigit():
                    quantity = int(items[0])
                    name = " ".join(items[0:])
                else:
                    # Default quantity is 1 if none is specified
                    quantity = 1
                    name = " ".join(items)

                # Add the parsed name and quantity to the dictionary
                if name:
                    result[name] = result.get(name, 0) + quantity

        return result

    def prompt_to_dish(self, prompt):
        embeds = self.encoder(prompt)

        # Type level
        similarities = {}
        for key, item in self.menu.items():
            similarities[key] = np.dot(embeds, item["encoding"])
        similarities = self.softmax(similarities)

        # dish_type = max(similarities, key=similarities.get)
        sorted_similarities = sorted(similarities, key=similarities.get, reverse=True)
        dish_types = sorted_similarities[:3]
        if similarities[dish_types[0]] < self.tsh:
            return None

        # dish name
        dish_options = {
            **self.menu[dish_types[0]]["sub_items"],
            **self.menu[dish_types[1]]["sub_items"],
            **self.menu[dish_types[2]]["sub_items"]
        }
        similarities = {}
        for key, item in dish_options.items():
            similarities[key] = np.dot(embeds, item["encoding"])
        dish_similarities = self.softmax(similarities)
        dish_name = max(dish_similarities, key=dish_similarities.get)
        if similarities[dish_name] < self.tsh:
            return None

        # optional changes
        optional_changes = dish_options[dish_name]["possible_changes"]
        no_change_similarity = similarities[dish_name]
        similarities = {}
        for change_name, change_embed in optional_changes.items():
            similarities[change_name] = np.dot(embeds, change_embed)
        similarities[dish_name] = no_change_similarity
        final_similarities = self.softmax(similarities)
        final_dish = max(final_similarities, key=final_similarities.get)
        return final_dish

    def softmax(self, similarities):
        values = np.array(list(similarities.values()))
        softmax_values = np.exp(values) / np.sum(np.exp(values))
        softmax_dict = dict(zip(similarities.keys(), softmax_values))
        return softmax_dict

    def __call__(self, text):
        order_dict = self.parse_string_to_dict(text)
        final_order = {}
        for key, items in order_dict.items():
            dish_name = self.prompt_to_dish(key)
            final_order[dish_name] = items
        return final_order

def start_models():
    har_path = "clip_text_encoder_vit_large.hef"
    config_file_path = "openai-clip-vit-large-patch14.npz"
    tokenizer_path = "openai/clip-vit-large-patch14"
    clip_call = CLIP(
        hef_path=har_path,
        config_file_path=config_file_path,
        tokenizer_path=tokenizer_path,
    )

    # audio_file = 'burger_with_cheese.m4a'
    model = whisper.load_model("small")
    
    return FeedMe(menu_path="feedme_db_burgers.npz", clip_text_encoder=clip_call), model
    

def parse_prompt(feeder, prompt):
    # result = model.transcribe(audio_file, language="English")
    # prompt = result["text"]

    print(f"you orderd {prompt}")
    output_order = feeder(prompt)
    print(f"you will get {output_order}")
    return output_order
