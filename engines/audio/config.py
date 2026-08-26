"""
Configuration Module
Central place to manage all system parameters
"""

from pathlib import Path

# Base directory for model artifacts and metadata
BASE_DIR = Path(__file__).resolve().parent

# ============================================================================
# AUDIO PROCESSING CONFIGURATION
# ============================================================================

# Sampling rate for audio loading (Hz)
AUDIO_SAMPLING_RATE = 16000

# Whether to trim silence from audio files
TRIM_SILENCE_ENABLED = False

# Threshold (dB) below reference to consider silence
SILENCE_TOP_DB = 40


# ============================================================================
# FEATURE EXTRACTION CONFIGURATION
# ============================================================================

# MFCC (Mel-Frequency Cepstral Coefficients)
MFCC_N_COEFFICIENTS = 13  # Number of MFCC coefficients to extract

# Mel Spectrogram
MEL_N_BANDS = 128  # Number of mel frequency bands


# ============================================================================
# FEATURE DIMENSIONS
# ============================================================================

# Total MFCC features: n_coefficients * 2 (mean + std)
MFCC_FEATURE_DIM = MFCC_N_COEFFICIENTS * 2  # 26

# Total Mel Spectrogram features: n_bands (mean only)
MEL_FEATURE_DIM = MEL_N_BANDS  # 128

# Phase 2 acoustic stats: NVAS + SPI + PNS + FAS (mean + std for each)
PHASE2_ADDITIONAL_FEATURE_DIM = 8

# Phase 3 features: Spectral Contrast (6 bands * 2) + ZCR (mean + std) + Chroma (12 * 2)
SPECTRAL_CONTRAST_DIM = 12
ZERO_CROSSING_RATE_DIM = 2
CHROMA_DIM = 24
PHASE3_ADDITIONAL_FEATURE_DIM = SPECTRAL_CONTRAST_DIM + ZERO_CROSSING_RATE_DIM + CHROMA_DIM

# Total feature vector dimension
TOTAL_FEATURE_DIM = MFCC_FEATURE_DIM + MEL_FEATURE_DIM + PHASE2_ADDITIONAL_FEATURE_DIM + PHASE3_ADDITIONAL_FEATURE_DIM  # 200


# ============================================================================
# DATASET CONFIGURATION
# ============================================================================

DATASET_ROOT = "./dataset"
DATASET_REAL_DIR = "real"
DATASET_FAKE_DIR = "fake"

# Expected number of files per class
EXPECTED_REAL_SAMPLES = 1000
EXPECTED_FAKE_SAMPLES = 1000
EXPECTED_TOTAL_SAMPLES = EXPECTED_REAL_SAMPLES + EXPECTED_FAKE_SAMPLES


# ============================================================================
# MODEL TRAINING CONFIGURATION
# ============================================================================

# Random Forest Classifier parameters
MODEL_N_ESTIMATORS = 150  # Number of trees in the forest
MODEL_MAX_FEATURES = "sqrt"  # Number of features to consider for best split
MODEL_MIN_SAMPLES_SPLIT = 2  # Minimum samples required to split a node
MODEL_MIN_SAMPLES_LEAF = 1  # Minimum samples required at leaf node
MODEL_MAX_DEPTH = None  # Maximum depth of tree (None = unlimited)
MODEL_RANDOM_STATE = 42  # Seed for reproducibility
MODEL_N_JOBS = -1  # Number of jobs to run in parallel (-1 = all cores)
MODEL_VERBOSE = 1  # Verbosity level

# Train-test split configuration
TRAIN_TEST_SPLIT_RATIO = 0.2  # Proportion of data for testing
TRAIN_RANDOM_STATE = 42  # Seed for reproducibility


# ============================================================================
# FEATURE SCALING CONFIGURATION
# ============================================================================

# StandardScaler parameters
SCALER_WITH_MEAN = True  # Center the data before scaling
SCALER_WITH_STD = True  # Scale the data to unit variance


# ============================================================================
# MODEL SAVING CONFIGURATION
# ============================================================================

MODEL_FILE_NAME = "deepfake_model.pkl"
SCALER_FILE_NAME = "scaler.pkl"
METADATA_FILE_NAME = "training_metadata.pkl"

# Absolute paths for model artifacts in the package directory
MODEL_FILE_PATH = str(BASE_DIR / MODEL_FILE_NAME)
SCALER_FILE_PATH = str(BASE_DIR / SCALER_FILE_NAME)
METADATA_FILE_PATH = str(BASE_DIR / METADATA_FILE_NAME)


# ============================================================================
# PREDICTION CONFIGURATION
# ============================================================================

# Output format for predictions
PREDICTION_OUTPUT_FORMAT = "{prediction} (NSRI: {nsri:.0f}%)"

# Class labels
CLASS_LABELS = {
    0: "Real",
    1: "Deepfake"
}


# ============================================================================
# LOGGING AND DISPLAY CONFIGURATION
# ============================================================================

# Print progress every N samples
PRINT_PROGRESS_INTERVAL = 100

# Display settings
DISPLAY_FEATURE_IMPORTANCE_TOP_K = 10  # Show top 10 important features


# ============================================================================
# VALIDATION THRESHOLDS
# ============================================================================

# Minimum expected accuracy
MIN_ACCEPTABLE_ACCURACY = 0.75  # 75%

# Maximum expected NaN ratio in features
MAX_NAN_RATIO = 0.01  # 1%


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def print_config():
    """Print all configuration values"""
    print("=" * 70)
    print("SYSTEM CONFIGURATION")
    print("=" * 70)
    
    print("\nAUDIO PROCESSING:")
    print(f"  Sampling Rate: {AUDIO_SAMPLING_RATE} Hz")
    print(f"  Trim Silence: {TRIM_SILENCE_ENABLED}")
    print(f"  Silence Threshold: {SILENCE_TOP_DB} dB")
    
    print("\nFEATURE EXTRACTION:")
    print(f"  MFCC Coefficients: {MFCC_N_COEFFICIENTS}")
    print(f"  MFCC Features: {MFCC_FEATURE_DIM} (mean + std)")
    print(f"  Mel Bands: {MEL_N_BANDS}")
    print(f"  Mel Features: {MEL_FEATURE_DIM}")
    print(f"  Total Features: {TOTAL_FEATURE_DIM}")
    
    print("\nDATASET:")
    print(f"  Root Directory: {DATASET_ROOT}")
    print(f"  Real Samples: {EXPECTED_REAL_SAMPLES}")
    print(f"  Fake Samples: {EXPECTED_FAKE_SAMPLES}")
    print(f"  Total Samples: {EXPECTED_TOTAL_SAMPLES}")
    
    print("\nMODEL:")
    print(f"  Algorithm: Random Forest")
    print(f"  Number of Trees: {MODEL_N_ESTIMATORS}")
    print(f"  Max Features: {MODEL_MAX_FEATURES}")
    print(f"  Max Depth: {MODEL_MAX_DEPTH}")
    print(f"  Random State: {MODEL_RANDOM_STATE}")
    print(f"  Model Path: {MODEL_FILE_PATH}")
    print(f"  Scaler Path: {SCALER_FILE_PATH}")
    print(f"  Metadata Path: {METADATA_FILE_PATH}")
    
    print("\nTRAINING:")
    print(f"  Train-Test Split: {TRAIN_TEST_SPLIT_RATIO*100:.0f}% test")
    print(f"  Train Size: {(1-TRAIN_TEST_SPLIT_RATIO)*100:.0f}%")
    print(f"  Test Size: {TRAIN_TEST_SPLIT_RATIO*100:.0f}%")
    
    print("\nFILES:")
    print(f"  Model: {MODEL_FILE_NAME}")
    print(f"  Scaler: {SCALER_FILE_NAME}")
    print(f"  Metadata: {METADATA_FILE_NAME}")
    
    print("\n" + "=" * 70 + "\n")


def get_config_summary():
    """Return configuration as dictionary"""
    return {
        'audio': {
            'sampling_rate': AUDIO_SAMPLING_RATE,
            'trim_silence': TRIM_SILENCE_ENABLED,
            'silence_top_db': SILENCE_TOP_DB
        },
        'features': {
            'mfcc_coefficients': MFCC_N_COEFFICIENTS,
            'mel_bands': MEL_N_BANDS,
            'total_features': TOTAL_FEATURE_DIM
        },
        'dataset': {
            'root': DATASET_ROOT,
            'total_samples': EXPECTED_TOTAL_SAMPLES
        },
        'model': {
            'algorithm': 'Random Forest',
            'n_estimators': MODEL_N_ESTIMATORS,
            'random_state': MODEL_RANDOM_STATE
        }
    }


if __name__ == "__main__":
    print_config()
