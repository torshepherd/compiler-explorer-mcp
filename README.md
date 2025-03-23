# Compiler Explorer MCP

A Model Context Protocol (MCP) server that connects LLMs to the Compiler Explorer API, enabling them to compile code, explore compiler features, and analyze optimizations across different compilers and languages.

## Example Questions

Here are some interesting questions you can ask your LLM using this MCP:

### Compiler Feature Exploration
- "What is the earliest version of GCC that supports the `#embed` directive?"
- "Show me how different versions of Clang handle C++20 modules"
- "What optimization flags are available in Clang 12 that weren't in Clang 11?"
- "Can you demonstrate how MSVC and GCC handle C++20 coroutines differently?"

### Optimization Analysis
- "What's the assembly difference between `-O2` and `-O3` for a simple recursive Fibonacci function in GCC 13?"
- "How does Clang's vectorization compare to GCC's for a basic matrix multiplication?"
- "Show me how different optimization levels affect tail-call optimization in this recursive function"
- "What's the impact of `-ffast-math` on this floating-point heavy computation?"

### Language Feature Support
- "Which C++20 features are supported in the latest versions of GCC, Clang, and MSVC?"
- "Show me how different compilers implement std::optional's memory layout"
- "Compare how GCC and Clang handle C++20's constexpr virtual functions"
- "Demonstrate the differences in how Intel and GCC compilers auto-vectorize SIMD operations"

### Assembly Deep Dives
- "What's the most efficient way to implement a population count in x86 assembly across different CPU architectures?"
- "Show me how different compilers optimize a simple string reverse function at -O3"
- "Compare the assembly output of a virtual function call vs a normal function call"
- "How do different compilers implement std::variant's type switching in assembly?"

### Cross-Language Comparison
- "Compare the generated assembly for the same algorithm in C++, Rust, and Go"
- "How do exception handling mechanisms differ between C++ and Rust in terms of generated code?"
- "Show me the overhead of Rust's bounds checking compared to unchecked C++ array access"
- "Compare how C++ and D implement RAII in terms of generated assembly"

### Performance Investigation
- "What's the assembly-level difference between using std::sort and a hand-written quicksort?"
- "Show me how different string concatenation methods compare in terms of generated instructions"
- "Compare the efficiency of std::map vs std::unordered_map operations in assembly"
- "How do different smart pointer implementations affect inlining and code size?"
