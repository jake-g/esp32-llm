# Running a LLM on the ESP32

A port of llama2.c for the ESP32-S3 microcontroller. This project implements a lightweight version of the Llama 2 architecture optimized for embedded systems.

**Changes so far:**
* tweaked the code in order to add a little bit more of randomness in the seed generation.
* support for tiny stories and aidreams260K (mc9625).
* upgraded to `esp-idf` version `5.5`
* disable harware display for now
* generate text for N generations

**Example Output**
```
Loading Model
I (540) MAIN: Initializing SPIFFS
I (620) MAIN: Partition size: total: 1920401, used: 1072021
I (620) MAIN: LLM Path is /data/stories260K.bin
I (620) LLM: Vocab size is 512
I (660) LLM: File size: 1056540 bytes
I (660) LLM: Free ram available: 2388432
I (1080) LLM: Successfully read LLM into memory
I (1080) LLM: Free ram available: 1307304
I (1080) LLM: Successfully read checkpoint
I (1130) LLM: Transformer successfully built
I (1130) LLM: Created FreeRTOS Tasks
I (1130) LLM: Vocab size is 512

I (1140) LLM: Opened Tokenizer File
I (1160) LLM: Tokenizer successfully built
I (1160) MAIN: Creating sampler with temperature=0.800000, topp=0.900000
I (1160) LLM: Building sampler with temperature: 0.800000, topp: 0.900000
I (1170) LLM: Sampler built with temperature: 0.800000, topp: 0.900000

Generating (1/10)
Once upon a time in Seattle, there was a little girl named Lily. She loved to eat all the animals and her mommy. One day, she went to a park to play with her friends. The park was very pretty and had a big box.
Lily's mommy brought her a picture of a tree. Lily was so happy and closed her eyes. She put the picture on her grandma's box. When she got there, she saw a big birdie. The bird was very scared of the bird and wanted to help the bird.
Lily started to cry and asked her mommy, "Can I play with your picture?" Her mommy said, "Yes, but be careful." Lily was happy to help her mommy. They played together every day.
Achieved tok/s: 18.587

Generating (2/10)
Once upon a time in Seattle, there was a little girl named Lily. She had a big, red ball that she loved to play with. One day, she went to the park to play with her friends.
As they walked, Lily saw a big bird flying in the sky. She wanted to go to her friend, so she climbed up the ball. But the bird was too small and didn't know what to do.
Lily's friend, Timmy, came over to play. "What are you doing?" asked Lily. "That's a good idea. It's a special bird."
Lily replied, "I'm sorry, Lily. I didn't know what to do."
The bird said, "I'm sorry, Lily. I didn't know what to do. I'm sorry to help you." Lily asked, "Don't worry, we can help the bird. We can help you."
The bird felt better and took the bird and Lily felt happy! She said, "Thank you, Timmy. You are a good friend." From that day on, Lily and the bird became good friends and played together every day.
Achieved tok/s: 14.282

Generating (3/10)
Once upon a time in Seattle, there was a little girl named Lily. She loved to play outside in the park with her friends. One day, she saw a big, red ball. She wanted to play with it, but the ball was too big.
Lily's friend, Tom, came over to play. "What are you doing?" she asked. 
"I want to play with me," said Lily. "It's okay to be careful."
Lily was very happy and said, "Yes, I will help you." 
They both sat down and laughed. They played together and had lots of fun. Then, they found a big green ball. Lily took the ball and put it on the ball. After a while, Lily's mom came into the room and saw the ball. She was so happy and hugged Lily. "Thank you, Lily!" she said. "You're welcome, Lily."
Achieved tok/s: 17.756
```


## Requirements

### Hardware
- ESP32-S3 development board
- Minimum 2MB PSRAM
- Minimum 4MB Flash

### Software
- ESP-IDF v4.5 or later
- Python 3.7 or later (for training and tokenizer)

## Installation

### VSCode Extension
* Install [ESP-IDF Prereqs](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/get-started/linux-macos-setup.html#step-1-install-prerequisites)
* Install and set up [ESP-IDF Extension](https://github.com/espressif/vscode-esp-idf-extension/blob/master/docs/tutorial/install.md)
  * express install latest release (master), default everything
  * main folder located `$HOME/esp/master/esp-idf/export.sh`
* Using ESP Extension with project dir `esp32-llm`
  * Build, Flash, Monitor, Clean, Select Board ect


### Manual
1. Clone this repository:
```bash
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
- and on fork [esp32-llm](https://github.com/mc9625/esp32-llm/) by mc9625
