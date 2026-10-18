#include <stdio.h>
#include <stdlib.h>
#include <inttypes.h>
#include "esp_spiffs.h"
#include "sdkconfig.h"
#include "esp_err.h"
#include "esp_log.h"
#include <time.h>
#include "llm.h"
#include <string.h>
#include "esp_random.h"


static const char *TAG = "MAIN";
#define NUM_GENERATIONS 10 // Constant for number of generations

/**
 * @brief intializes SPIFFS storage
 * 
 */
void init_storage(void)
{

    ESP_LOGI(TAG, "Initializing SPIFFS");

    esp_vfs_spiffs_conf_t conf = {
        .base_path = "/data",
        .partition_label = NULL,
        .max_files = 5,
        .format_if_mount_failed = false};

    esp_err_t ret = esp_vfs_spiffs_register(&conf);

    if (ret != ESP_OK)
    {
        if (ret == ESP_FAIL)
        {
            ESP_LOGE(TAG, "Failed to mount or format filesystem");
        }
        else if (ret == ESP_ERR_NOT_FOUND)
        {
            ESP_LOGE(TAG, "Failed to find SPIFFS partition");
        }
        else
        {
            ESP_LOGE(TAG, "Failed to initialize SPIFFS (%s)", esp_err_to_name(ret));
        }
        return;
    }

    size_t total = 0, used = 0;
    ret = esp_spiffs_info(NULL, &total, &used);
    if (ret != ESP_OK)
    {
        ESP_LOGE(TAG, "Failed to get SPIFFS partition information (%s)", esp_err_to_name(ret));
    }
    else
    {
        ESP_LOGI(TAG, "Partition size: total: %d, used: %d", total, used);
    }
}

/**
 * @brief Outputs to display
 * 
 * @param text The text to output
 */
void write_display(char *text)
{
    
}

static float last_tok_s = 0.0f; // throughput of the most recent generation

/**
 * @brief Callbacks once generation is done
 * 
 * @param tk_s The number of tokens per second generated
 */
void generate_complete_cb(float tk_s)
{
    last_tok_s = tk_s; // TODO connect display
}

/**
 * @brief Generates a 64-bit random seed via  ESP RNG for initializing a PRNG.
 * 
 */
unsigned long long get_random_seed(void) {
    // Get a high-quality 64-bit seed combining two 32-bit values
    unsigned long long high = esp_random();
    unsigned long long low = esp_random();
    unsigned long long seed = (high << 32) | low;
    
    // Add a small amount of time-based entropy
    seed ^= (unsigned long long)time(NULL);
    
    // Make sure we never return 0 or small values
    if (seed < 1000000) {
        seed += 1000000;
    }
    
    return seed;
}

/**
 * @brief Reads one line without its trailing newline; returns 0 at EOF.
 */
static int read_line(FILE *f, char *buf, size_t len)
{
    if (fgets(buf, len, f) == NULL)
        return 0;
    buf[strcspn(buf, "\r\n")] = '\0';
    return 1;
}

void app_main(void)
{
    
    ESP_LOGI(TAG, "Loading Model");
    init_storage();

    // default parameters
    // char *checkpoint_path = "/data/aidreams260K.bin"; // e.g. out/model.bin
    char *checkpoint_path = "/data/stories260K.bin"; // e.g. out/model.bin
    char *tokenizer_path = "/data/tok512_stories.bin";
    float temperature = 0.9f;        // 0.0 = greedy deterministic. 1.0 = original. don't set higher
    float topp = 0.9f;               // top-p in nucleus sampling. 1.0 = off. 0.9 works well, but slower
    int steps = 1024;                 // number of steps to run for
    char *prompt = "Once upon a time in Seattle";             // prompt string

    // Self-test: greedy decoding is deterministic, so the board must reproduce
    // karpathy/llama2.c run.c on the host:
    //   ./run stories260K.bin -z tok512_stories.bin -t 0 -n 48 -i "Once upon a time"
    // stories260K runs at about 20 tok/s; far below 10 means PSRAM, cache or
    // CPU frequency are misconfigured.
    static char st_prompt[256] = "Once upon a time";
    static char st_golden[512] =
        "Once upon a time, there was a little girl named Lily. She loved to play "
        "outside in the park. One day, she saw a big, red ball. She wanted to";
    int st_steps = 48;

    // A custom model ships /data/model.bin, /data/tokenizer.bin and
    // /data/selftest.txt (line 1: steps, line 2: prompt, line 3: golden from
    // `run model.bin -z tokenizer.bin -t 0 -n <steps> -i "<prompt>"`).
    static char st_steps_line[16];
    FILE *st = fopen("/data/selftest.txt", "r");
    if (st != NULL)
    {
        int ok = read_line(st, st_steps_line, sizeof(st_steps_line)) &&
                 read_line(st, st_prompt, sizeof(st_prompt)) &&
                 read_line(st, st_golden, sizeof(st_golden));
        fclose(st);
        if (!ok)
        {
            ESP_LOGE(TAG, "Malformed /data/selftest.txt");
            return;
        }
        st_steps = atoi(st_steps_line);
        checkpoint_path = "/data/model.bin";
        tokenizer_path = "/data/tokenizer.bin";
        prompt = st_prompt;
    }
    // In app_main
    unsigned long long rng_seed = get_random_seed();

    if (rng_seed <= 0) {
        // Use time as base, but mix in some hardware entropy
        rng_seed = (unsigned long long)time(NULL);
        // XOR with a single hardware random value
        rng_seed ^= esp_random();
    }



    // build the Transformer via the model .bin file
    Transformer transformer;
    ESP_LOGI(TAG, "LLM Path is %s", checkpoint_path);
    build_transformer(&transformer, checkpoint_path);
    if (steps == 0 || steps > transformer.config.seq_len)
        steps = transformer.config.seq_len; // override to ~max length

    // build the Tokenizer via the tokenizer .bin file
    Tokenizer tokenizer;
    build_tokenizer(&tokenizer, tokenizer_path, transformer.config.vocab_size);

    if (st_steps == 0 || st_steps > transformer.config.seq_len)
        st_steps = transformer.config.seq_len;
    static char selftest_out[512];
    Sampler greedy;
    build_sampler(&greedy, transformer.config.vocab_size, 0.0f, topp, rng_seed);
    generate(&transformer, &tokenizer, &greedy, st_prompt, st_steps, selftest_out,
             sizeof(selftest_out), &generate_complete_cb);
    free_sampler(&greedy);
    int golden_ok = strcmp(selftest_out, st_golden) == 0;
    int selftest_ok = golden_ok && last_tok_s >= 10.0f;
    printf("LLM_SELFTEST {\"ok\":%s,\"golden\":%s,\"tok_s\":%.2f}\n", selftest_ok ? "true" : "false",
           golden_ok ? "true" : "false", last_tok_s);
    if (!selftest_ok)
    {
        return;
    }

    // build the Sampler
    Sampler sampler;
    ESP_LOGI(TAG, "Creating sampler with temperature=%f, topp=%f", temperature, topp);
    build_sampler(&sampler, transformer.config.vocab_size, temperature, topp, rng_seed);

    // run multiple generations!
    for (int i = 0; i < NUM_GENERATIONS; i++)
    {
        ESP_LOGI(TAG, "Generating (%d/%d)", i + 1, NUM_GENERATIONS);
        generate(&transformer, &tokenizer, &sampler, prompt, steps, NULL, 0, &generate_complete_cb);
        printf("LLM_RESULT {\"gen\":%d,\"tok_s\":%.2f}\n", i + 1, last_tok_s);
    }
}
