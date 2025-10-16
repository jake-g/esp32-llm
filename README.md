# Running a LLM on the ESP32

A port of llama2.c for the ESP32-S3 microcontroller. This project implements a lightweight version of the Llama 2 architecture optimized for embedded systems. See [parent repository](https://github.com/jake-g/micro-llm) for more details on training custom models.


<img src="https://imgur.com/XuHewD5.png" width="200">

**Changelog:**
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

## Performance

Current performance metrics:
- Inference speed: ~17 tokens/second
- Memory efficiency: Uses optimized data structures and FreeRTOS tasks

## Memory Usage

*   **Flash (SPIFFS):** ~1.05 MB (Model + Tokenizer files)
*   **PSRAM (Heap):**
    *   ~1.0 MB for Model Weights (static).
    *   ~1.0 MB for RunState/KV-Cache (dynamic, allocated at startup).
    *   Total PSRAM required: ~2.5 MB (leaving headroom for ESP-IDF overhead).
*   **Internal SRAM:** Used for FreeRTOS stacks, DMA buffers, and high-speed temporary variables.

## Technical Details

This project ports the Llama 2 transformer architecture to the ESP32-S3, utilizing specific hardware acceleration and FreeRTOS features to achieve workable inference speeds on an embedded microcontroller.

### The Inference Pipeline

The text generation process follows a standard LLM pipeline, adapted for C and embedded constraints:

1.  **Tokenizer (BPE):** The input string prompt is converted into a sequence of integer tokens using Byte Pair Encoding (BPE). The vocabulary is kept very small (512 tokens) to minimize the size of the embedding weights and output logits.
2.  **Transformer Forward Pass:**
    *   **Embedding:** The input token is converted into a vector of dimension `dim` (64).
    *   **Layers:** The model iterates through `n_layers` (5). Each layer consists of:
        *   RMSNorm (Root Mean Square Normalization).
        *   **Multi-Query Attention (MQA):** Computes Query, Key, and Value vectors. Applies Rotary Positional Embeddings (RoPE) to Q and K. Updates the KV-Cache. Computes attention scores and the weighted sum of values.
        *   **Feed-Forward Network (FFN):** A SwiGLU (SiLU gated linear unit) network that expands the dimension to `hidden_dim` and projects it back down.
        *   Residual connections after Attention and FFN blocks.
    *   **Classifier:** The final output vector is normalized and projected via matrix multiplication into logits (size of vocabulary).
3.  **Sampler:** The logits are converted into probabilities via Softmax. A token is selected using **Top-P (Nucleus) Sampling** and **Temperature** scaling to introduce controlled randomness. High-quality entropy from the ESP32 hardware RNG is used to seed the sampling process.
4.  **Detokenizer:** The selected integer token is mapped back to its corresponding string piece and output to the console.
5.  **Autoregression:** The newly generated token becomes the input for the next iteration.

### ESP32-S3 Optimizations

To fit a transformer model into the limited resources of an MCU, several specific optimizations are employed:

#### 1. Hardware Acceleration (DSP)
The ESP32-S3 includes vector instructions meant for signal processing. This project utilizes the `esp-dsp` library, specifically `dsps_dotprod_f32_aes3`, to hardware-accelerate floating-point dot products. This is the bottleneck operation in matrix multiplications (MatMul) throughout the transformer.

#### 2. Dual-Core Parallelization via FreeRTOS
The inference engine does not run solely as a single-threaded process. It leverages the ESP32-S3's dual cores using FreeRTOS primitives:
*   **Pinned Tasks:** Specific compute-heavy tasks (`matmul_task`, `forward_task`) are pinned to Core 1, while the main application logic runs on Core 0.
*   **Synchronization:** `EventGroup` and `Semaphore` are used to coordinate data dependency between layers. For example, the multi-head attention mechanism splits work, signaling via semaphores when blocks of data are ready for the next stage of computation.

#### 3. Memory Management (PSRAM)
The ESP32-S3's internal SRAM is insufficient for even tiny LLMs.
*   **Model Weights:** The `.bin` model file is read from SPIFFS storage and loaded entirely into external PSRAM via `malloc`.
*   **RunState (KV Cache):** The dynamic memory required during inference (activations and the Key-Value cache) is allocated in PSRAM.

### Model Specifications & Memory Footprint

How does it fit in ~3MB of usable memory? The architecture is aggressively scaled down based on the "TinyStories" datasets.

*   **Vocabulary Size:** **512 tokens**. Standard LLMs use 32k to 100k. A standard vocab (32000) with a dimension of 64 would require a 7.6MB embedding table alone. By reducing vocab to 512, the embedding table and final classifier weights are negligible in size.
*   **Context Window:** **512 tokens**. This is the model's "short-term memory." It can recall and attend to the previous 512 tokens generated or provided in the prompt.
*   **Data Type:** Full precision `float32`.
*   **KV Cache Size:** The memory required to store past context grows with sequence length.
    $$ \text{Size} = 2 \times n\_layers \times seq\_len \times kv\_dim \times 4 \text{ bytes} $$
    With current parameters, the KV cache occupies a significant portion of the allocated run state in PSRAM, enabling the 512-token context.


### Original [llama2.c](https://github.com/karpathy/llama2.c): vs. ESP32 Port: [micro-llm](https://github.com/jake-g/micro-llm) 

Analysis of the changes made to port Andrej Karpathy's original single-file C implementation in [`run.c`](https://github.com/karpathy/llama2.c/blob/master/run.c) to a hardware-accelerated, multi-core library for the ESP32-S3 microcontroller, found in the [esp32-llm](https://github.com/jake-g/esp32-llm) project's [`llm.c`](https://github.com/jake-g/esp32-llm/blob/main/main/llm.c) and [`llm.h`](https://github.com/jake-g/esp32-llm/blob/main/main/llm.h). 
The port re-architects the original code to leverage the specific features of a real-time embedded environment.

### Memory Architecture & Model Loading

The port's primary challenge was adapting to a microcontroller's memory model, which lacks an MMU and virtual memory.

*   **From Memory-Mapping to Direct Loading:** The original `run.c` uses `mmap()` to map the model file into virtual memory. The ESP32 port replaces this by reading the model from a SPIFFS filesystem directly into a `malloc`'d buffer in external PSRAM.
    ```c
    // Original mmap() approach in run.c
    *data = mmap(NULL, *file_size, PROT_READ, MAP_PRIVATE, *fd, 0);
    ```
    ```c
    // ESP32 Port: Manual load from SPIFFS into PSRAM
    *data = malloc(*file_size);
    fread(*data, 1, *file_size, file);
    ```

*   **Compatibility Shims:** To minimize code changes, POSIX functions like `munmap` are redefined as macros that call `free()` or do nothing, preserving the original structure.
    ```c
    #define munmap(ptr, length) custom_munmap(ptr) // custom_munmap calls free()
    #define close(fd) custom_close(fd)             // custom_close does nothing
    ```
*   **Memory Debugging:** The port uses `esp_get_free_heap_size()` during loading to log available PSRAM, a critical step for debugging on a resource-constrained device.

### Performance: Parallelism & Hardware Acceleration

The port replaces OpenMP with an explicit dual-core implementation using FreeRTOS and ESP-IDF's hardware libraries.

#### Matrix Multiplication (`matmul`)

The `matmul` function, the main performance bottleneck, is heavily optimized.

1.  **Hardware-Accelerated Dot Product:** The C `for` loop for dot products is replaced by a single call to the `esp-dsp` library, which uses the ESP32-S3's vector instructions.
    *   **Original [`run.c`](https://github.com/karpathy/llama2.c/blob/master/run.c):**
        ```c
        for (int j = 0; j < n; j++) {
            val += w[i * n + j] * x[j];
        }
        ```    
    *   **ESP32 Port [`llm.c`](https://github.com/jake-g/esp32-llm/blob/main/main/llm.c):**
        
        ```c
        dsps_dotprod_f32_aes3(row, x, &val, n);
        ```
2.  **RTOS-based Parallelization:** Instead of `#pragma omp parallel for`, the port uses a persistent FreeRTOS task (`matmul_task`) pinned to Core 1. The `matmul` function on Core 0 computes the first half of the work, signals the task via a semaphore to compute the second half, and then uses an event group to sync both cores before returning.

#### Multi-Head Attention (`forward`)
The same manual parallelization pattern is applied to the multi-head attention loop. The `for` loop over heads is split, with Core 0 and a dedicated `forward_task` on Core 1 each processing half the workload concurrently.

### Generation Loop & Sampler Enhancements

The port adds features to make the LLM a reusable and robust application component.

*   **High-Quality Randomness:** The RNG is seeded with the ESP32's hardware true random number generator via `esp_random()` instead of `time(NULL)`.

*   **State Management for Continuous Generation:** A new `reset_run_state()` function uses `memset` to efficiently clear activation and KV-cache buffers, allowing for multiple generations without reloading the model.

*   **Application Callback API:** The `generate` function accepts a callback pointer (`generated_complete_cb`) which is invoked upon completion. This decouples the LLM engine from the main application logic.

*   **Sampler Logic:** The port standardizes on Top-P (`sample_topp`) sampling for its stability, removing the original's fallback to multinomial sampling. **TODO:** Investigate re-enabling `sample_mult` as an option for specific use cases where `topp >= 1.0`.

### ESP32-S3 Specific Optimizations

The port's performance relies on features unique to the ESP32-S3 and its SDK.

*   **Vector Instructions (SIMD):** The `dsps_dotprod_f32_aes3` function compiles to assembly that uses the ESP32-S3's SIMD hardware. This allows the CPU to perform calculations on a vector of floats in a single clock cycle, providing a massive speedup over scalar operations.

*   **Memory Alignment for Vectorization:** Using SIMD instructions requires strict memory alignment. The custom `v4sf` type ensures this. The `__attribute__((aligned(16)))` directive forces the compiler to place these variables on 16-byte boundaries, satisfying the hardware requirement.
    ```c
    typedef float v4sf __attribute__((aligned(16)));
    ```

*   **FreeRTOS Core Affinity:** The compute-heavy tasks are explicitly pinned to Core 1 using `xTaskCreatePinnedToCore`. This isolates the inference workload, leaving Core 0 free for application logic and system services (like networking), resulting in more predictable performance. **TODO:** The fixed 2048-byte stack for these tasks should be profiled to optimize SRAM usage.
    ```c
    xTaskCreatePinnedToCore(matmul_task, "MatMul2", 2048, ..., 1); // Pin to Core 1
    ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Based on [llama2.c](https://github.com/karpathy/llama2.c) by Andrej Karpathy
- and on [esp32-llm](https://github.com/DaveBben/esp32-llm) by Dave Bennet
- and on fork [esp32-llm](https://github.com/mc9625/esp32-llm/) by mc9625
