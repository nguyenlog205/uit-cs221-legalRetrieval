from ..utils import extract_config

class IntentionClassifier():
    def __init__(
        self,
        config_path:str,
    ):
        configs = extract_config(config_path)
        self.MODEL_NAME  = configs['IntentionClassifier']['model_name']
        
        return 