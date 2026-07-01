import sys

target = 'arch/arm64/kernel/cpuinfo.c'
print(f"Reading {target}...")

with open(target) as f:
    content = f.read()

# 1. 先确认包含 c_show
if 'c_show' not in content:
    print("ERROR: c_show not found!")
    sys.exit(1)

# 2. 找到函数起始位置
pos = content.find('static int c_show(struct seq_file *m, void *v)')
if pos < 0:
    pos = content.find('static int c_show (struct seq_file *m, void *v)')
if pos < 0:
    pos = content.find('int c_show(struct seq_file *m')
if pos < 0:
    print(f"ERROR: c_show signature not found. Searching for 'c_show'...")
    # Print surrounding context
    idx = content.find('c_show')
    if idx >= 0:
        print(f"Found 'c_show' at position {idx}:")
        print(content[max(0,idx-50):idx+200])
    sys.exit(1)

print(f"Found c_show at position {pos}")

# 3. 找到函数结束 (匹配大括号)
brace_count = 0
end = -1
for i in range(pos, len(content)):
    if content[i] == '{':
        brace_count += 1
    elif content[i] == '}':
        brace_count -= 1
        if brace_count == 0:
            end = i + 1
            break

if end < 0:
    print("ERROR: Could not find end of function")
    sys.exit(1)

print(f"Function ends at position {end}, length={end-pos}")

# 4. 新函数体
new_func = """static int c_show(struct seq_file *m, void *v)
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

# 5. 替换
new_content = content[:pos] + new_func + content[end:]
with open(target, 'w') as f:
    f.write(new_content)

# 6. 验证
with open(target) as f:
    check = f.read()
if 'fake_midr' in check and 'HiSilicon Kirin 9020' in check:
    print("VERIFIED: cpuinfo patched!")
else:
    print("FAILED!")

# 7. 打印确认行
import os
os.system("grep -c 'fake_midr' " + target)
os.system("grep -c 'Kirin 9020' " + target)
