import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning, module=r"coremltools(\.|$)")
warnings.filterwarnings("ignore", message=r"invalid escape sequence.*\\_", category=SyntaxWarning)
from bottled_kraken import main
if __name__ == '__main__':
    main()
