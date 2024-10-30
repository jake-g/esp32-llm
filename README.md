# Little AI Dreamer based on llama2-esp32

A port of llama2.c for the ESP32-S3 microcontroller. This project implements a lightweight version of the Llama 2 architecture optimized for embedded systems.

This project is aimed to create a very simple AI Dreaming Machine. The only thing this code does is generate little AI dreams.But it does it in only 512Kb of memory on a very underpowered micro controller.

## Features

- Runs on ESP32-S3 with minimal resources
- Custom vocabulary size of 512 tokens
- Optimized model architecture for embedded systems:
  - Dimension: 64
  - Layers: 4
  - Heads: 4
  - KV Heads: 4
  - Max Sequence Length: 128
  - Multiple of: 4

## Requirements

### Hardware
- ESP32-S3 development board
- Minimum 2MB PSRAM
- Minimum 4MB Flash

### Software
- ESP-IDF v4.4 or later
- Python 3.7 or later (for training and tokenizer)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/mc9625/llama2-esp32.git
cd llama2-esp32
```

2. Set up ESP-IDF environment:
```bash
. $HOME/esp/esp-idf/export.sh
```

3. Configure the project:
```bash
idf.py set-target esp32s3
idf.py menuconfig
```

4. Build and flash:
```bash
idf.py build
idf.py -p /dev/ttyUSB0 flash
```

## Model Configuration

The current model uses these parameters:
```
--vocab_source=custom
--vocab_size=512
--dim=64
--n_layers=4
--n_heads=4
--n_kv_heads=4
--multiple_of=4
--max_seq_len=128
--batch_size=128
```

## Project Structure

- `src/llm.c` - Main LLM implementation
- `src/llm.h` - Header file with data structures and function declarations
- `src/main.c` - ESP32 application entry point
- `components/` - External components and dependencies

## Memory Usage

- Flash: ~XMB for model weights
- PSRAM: ~YKB for runtime buffers
- RAM: ~ZKB for stack and heap

## Performance

Current performance metrics:
- Inference speed: ~17 tokens/second
- Memory efficiency: Uses optimized data structures and FreeRTOS tasks

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Based on [llama2.c](https://github.com/karpathy/llama2.c) by Andrej Karpathy
- and on [esp32-llm](https://github.com/DaveBben/esp32-llm) by Dave Bennet
- ESP32 port developed by Massimo Di Leo

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
