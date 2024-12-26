import json
import itertools
import numpy as np
from transformers import CLIPTokenizer
from hailo_platform import (HEF, Device, VDevice, HailoStreamInterface, InferVStreams, ConfigureParams,
                InputVStreamParams, OutputVStreamParams, FormatType)


def configure_and_get_network_group(hef, target):
    configure_params = ConfigureParams.create_from_hef(hef, interface=HailoStreamInterface.PCIe)
    network_group = target.configure(hef, configure_params)[0]
    return network_group

def create_input_output_vstream_params(network_group):
    input_vstreams_params = InputVStreamParams.make_from_network_group(network_group, quantized=False, format_type=FormatType.FLOAT32)
    output_vstreams_params = OutputVStreamParams.make_from_network_group(network_group, quantized=False, format_type=FormatType.FLOAT32)
    return input_vstreams_params, output_vstreams_params


def print_input_output_vstream_info(hef):
    input_vstream_info = hef.get_input_vstream_infos()
    output_vstream_info = hef.get_output_vstream_infos()
    return input_vstream_info, output_vstream_info

class CLIP:
    def __init__(self, hef_path, config_file_path, tokenizer_path):
        config = np.load(config_file_path) 
        self.text_projection = config["projection_layer"]
        self.text_embeddings = config["text_embeddings"]
        self.tokenizer = CLIPTokenizer.from_pretrained(tokenizer_path)
        self.hef = HEF(hef_path)
        self.devices = Device.scan()
        self.target = VDevice(device_ids=self.devices)
        self.network_group = configure_and_get_network_group(self.hef, self.target)
        self.network_group_params = self.network_group.create_params()
        self.input_vstreams_params, self.output_vstreams_params = create_input_output_vstream_params(self.network_group)
        self.input_vstream_info, self.output_vstream_info = print_input_output_vstream_info(self.hef)
    def text_encoder_preprocessing(self, prompt):
        return self.tokenizer(
            prompt,
            padding="max_length",   # Pad to the model's maximum sequence length
            truncation=True,        # Truncate if the text exceeds the maximum length
            max_length=77,          # CLIP typically uses 77 tokens for text
            return_tensors="tf"     # Return PyTorch tensors (use "tf" for TensorFlow))
        )

    def text_encoding_postprocessing(self, logits, length):
        result = logits @ self.text_projection.T
        result = result[:length]
        result = result/ np.linalg.norm(result, axis=-1, keepdims=True)
        return np.mean(result, axis=-2)

    def infer_hw(self, x):
        with InferVStreams(self.network_group, self.input_vstreams_params, self.output_vstreams_params) as infer_pipeline:
            input_data = {self.input_vstream_info[0].name: x}
            with self.network_group.activate(self.network_group_params):
                output = infer_pipeline.infer(x)
        return output[self.output_vstream_info[0].name]
    
    def __call__(self, text):
        preproc = self.text_encoder_preprocessing(text)
        tokens = np.array(preproc['input_ids'])
        length = np.sum(preproc['attention_mask'] > 0) - 1
        x = np.expand_dims(self.text_embeddings[tokens], axis=0)
        outputs = self.infer_hw(x)
        embeds = self.text_encoding_postprocessing(outputs, length)
        return embeds[0, 0]


    
if __name__ == "__main__":
    har_path = 'hackathon/clip_text_encoder_vit_large.har'
    config_file_path = '/data/data/adk_models_files/models_files/clip/vit_large/coco_10xtd/2024-08-25/openai-clip-vit-large-patch14.npz'
    tokenizer_path = "openai/clip-vit-large-patch14"
    feedme_db = CLIP(har_path, config_file_path, tokenizer_path)
    feedme_db.build_encoding_db("hackathon/final_menu.json", "hackathon/feedme_db.npz")
    print("Done building FeedMeDB.")