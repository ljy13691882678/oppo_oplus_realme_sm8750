import re

with open('arch/arm64/kernel/cpuinfo.c') as f:
    content = f.read()

new_c_show = """static int c_show(struct seq_file *m, void *v)
{
    int i;
    static const u32 fake_midr[] = {
        (0x48U << 24) | (0x1U << 20) | (0xfU << 16) | (0xd0eU << 4) | 0x0U,
        (0x48U << 24) | (0x2U << 20) | (0xfU << 16) | (0xd0fU << 4) | 0x0U,
        (0x48U << 24) | (0x2U << 20) | (0xfU << 16) | (0xd0fU << 4) | 0x0U,
        (0x48U << 24) | (0x2U << 20) | (0xfU << 16) | (0xd0fU << 4) | 0x0U,
        (0x48U << 24) | (0x3U << 20) | (0xfU << 16) | (0xd10U << 4) | 0x0U,
        (0x48U << 24) | (0x3U << 20) | (0xfU << 16) | (0xd10U << 4) | 0x0U,
        (0x48U << 24) | (0x3U << 20) | (0xfU << 16) | (0xd10U << 4) | 0x0U,
        (0x48U << 24) | (0x3U << 20) | (0xfU << 16) | (0xd10U << 4) | 0x0U,
    };
    for_each_online_cpu(i) {
        u32 midr = (i < ARRAY_SIZE(fake_midr)) ? fake_midr[i] : fake_midr[ARRAY_SIZE(fake_midr)-1];
        seq_printf(m, "processor\\t: %d\\n", i);
        seq_printf(m, "Processor\\t: AArch64 Processor rev %d (aarch64)\\n", MIDR_REVISION(midr));
        seq_printf(m, "BogoMIPS\\t: 26.00\\n");
        seq_puts(m, "Features\\t: fp asimd evtstrm aes pmull sha1 sha2 crc32 atomics fphp asimdhp\\n");
        seq_printf(m, "CPU implementer\\t: 0x%02x\\n", MIDR_IMPLEMENTOR(midr));
        seq_printf(m, "CPU architecture: 8\\n");
        seq_printf(m, "CPU variant\\t: 0x%x\\n", MIDR_VARIANT(midr));
        seq_printf(m, "CPU part\\t: 0x%03x\\n", MIDR_PARTNUM(midr));
        seq_printf(m, "CPU revision\\t: %d\\n\\n", MIDR_REVISION(midr));
    }
    seq_printf(m, "Hardware\\t: HiSilicon Kirin 9020\\n");
    return 0;
}"""

# Method 1: Try regex
match = re.search(r'static int c_show$struct seq_file \*m, void \*v$', content)
if not match:
    print("ERROR: c_show() not found in cpuinfo.c!")
    exit(1)

start = match.start()
# Find the closing brace of the function
brace_count = 0
end = start
in_func = False
for i in range(start, len(content)):
    if content[i] == '{':
        brace_count += 1
        in_func = True
    elif content[i] == '}':
        brace_count -= 1
        if in_func and brace_count == 0:
            end = i + 1
            break

if end <= start:
    print("ERROR: Could not find end of c_show()")
    exit(1)

# Include trailing newline
while end < len(content) and content[end] in '\n\r':
    end += 1

print(f"c_show() found: chars {start} to {end}, replacing...")

new_content = content[:start] + new_c_show + '\n\n' + content[end:]

with open('arch/arm64/kernel/cpuinfo.c', 'w') as f:
    f.write(new_content)

# Verify
with open('arch/arm64/kernel/cpuinfo.c') as f:
    verify = f.read()

if 'fake_midr' in verify and 'HiSilicon Kirin 9020' in verify:
    print('VERIFIED: cpuinfo patched successfully!')
else:
    print('FAILED: patch not applied!')
    exit(1)
