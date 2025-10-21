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

Once upon a time, Jake went to the park. He saw a big gray box. He wanted to see what was inside. He wanted to see what was inside.
The boy got scared and ran to the garden. He saw a big bug on the ground. He wanted to show the bug. He picked up the bug. He put the bug on the bug and started to bug.
The bug was very happy. He went to the bug and said, "Thank you!" The bug was happy to see the bug. The bug was happy too. It was the bug.
Achieved tok/s: 19.393
I (12770) MAIN: Generating (2/10)
Once upon a time, Jake was very scared. He wanted to set it in the tree. He wanted to see what was inside. He wanted to see what was in the slide.
Jack said, "I want to see what's that?"
That night, Jack and his mom went to the park. They saw a small plant in the sky. The ball opened the ball and found the ball. The ball was on the slide. The ball was very happy.
Jack and the ball ran away. They were happy. They played together all day. They had many friends.
Achieved tok/s: 17.558
I (30230) MAIN: Generating (3/10)
Once upon a time, Jake was very sleepy. He was very excited to see him. He wanted to see what was going to do. But he did not want to share his toys.
Jack saw a bear and wanted to climb the tree. He said, "It's okay, Jack. You can climb the tree."
Jack was happy to help the bear. He went to the tree and said, "I want to play with your toys." His mom smiled and said, "Hello, Jack. You are very special your toy."
Jack was happy to have a new toy. He wished he had a great time. He went to the tree with his toys and showed him the toy.
Achieved tok/s: 16.408
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
4.  **Decoder:** The selected integer token is mapped back to its corresponding string piece and output to the console.
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
