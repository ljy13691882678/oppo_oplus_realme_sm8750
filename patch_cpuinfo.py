import sys, re

# ===== 1. 伪装 /proc/cpuinfo 中的 c_show() =====
target = 'arch/arm64/kernel/cpuinfo.c'
print(f"[1/2] Patching {target}...")

with open(target) as f:
    content = f.read()

pos = content.find('static int c_show(struct seq_file *m, void *v)')
if pos < 0:
    pos = content.find('int c_show(struct seq_file *m')
if pos < 0:
    print("ERROR: c_show not found!")
    sys.exit(1)

print(f"  Found at pos {pos}")

brace_count = 0
end = -1
for i in range(pos, len(content)):
    if content[i] == '{': brace_count += 1
    elif content[i] == '}':
        brace_count -= 1
        if brace_count == 0:
            end = i + 1
            break

new_func = """static int c_show(struct seq_file *m, void *v)
{
    int i;

    /*
     * Spoof CPU info -> HUAWEI Pura 90 Pro Max (Kirin9030S)
     * CPU0-3: part=0xd24 (mid-core), CPU4-6: part=0xd47 (big-core)
     * CPU7:   part=0xd06 (small-core)
     * All: implementer=0x48 (HiSilicon), variant=0x2, rev=0
     */
    static const u32 fake_midr[] = {
        (0x48U << 24) | (0x2U << 20) | (0xfU << 16) | (0xd24U << 4) | 0x0U,
        (0x48U << 24) | (0x2U << 20) | (0xfU << 16) | (0xd24U << 4) | 0x0U,
        (0x48U << 24) | (0x2U << 20) | (0xfU << 16) | (0xd24U << 4) | 0x0U,
        (0x48U << 24) | (0x2U << 20) | (0xfU << 16) | (0xd24U << 4) | 0x0U,
        (0x48U << 24) | (0x2U << 20) | (0xfU << 16) | (0xd47U << 4) | 0x0U,
        (0x48U << 24) | (0x2U << 20) | (0xfU << 16) | (0xd47U << 4) | 0x0U,
        (0x48U << 24) | (0x2U << 20) | (0xfU << 16) | (0xd47U << 4) | 0x0U,
        (0x48U << 24) | (0x2U << 20) | (0xfU << 16) | (0xd06U << 4) | 0x0U,
    };

    for_each_online_cpu(i) {
        u32 midr = (i < ARRAY_SIZE(fake_midr))
                   ? fake_midr[i]
                   : fake_midr[ARRAY_SIZE(fake_midr) - 1];

        seq_printf(m, "Processor\\t: AArch64 Processor rev %d (aarch64)\\n",
                   MIDR_REVISION(midr));
        seq_printf(m, "processor\\t: %d\\n", i);
        seq_printf(m, "BogoMIPS\\t: 2000.00\\n");
        seq_puts(m, "Features\\t: fp asimd evtstrm aes pmull sha1 sha2 "
                    "crc32 atomics fphp asimdhp cpuid asimdrdm jscvt fcma "
                    "lrcpc dcpop sha3 sm3 sm4 asimddp sha512 sve asimdfhm "
                    "dit uscat ilrcpc flagm ssbs sb paca pacg dcpodp flagm2 "
                    "frint svei8mm svebf16 i8mm bf16 dgh bti\\n");
        seq_printf(m, "CPU implementer\\t: 0x%02x\\n",
                   MIDR_IMPLEMENTOR(midr));
        seq_printf(m, "CPU architecture: 8\\n");
        seq_printf(m, "CPU variant\\t: 0x%x\\n", MIDR_VARIANT(midr));
        seq_printf(m, "CPU part\\t: 0x%03x\\n", MIDR_PARTNUM(midr));
        seq_printf(m, "CPU revision\\t: %d\\n", MIDR_REVISION(midr));
        seq_printf(m, "CPU physical\\t: %d\\n\\n", i);
    }

    seq_printf(m, "Hardware\\t: HUAWEI Pura 90 Pro Max\\n");

    return 0;
}"""

new_content = content[:pos] + new_func + content[end:]
with open(target, 'w') as f:
    f.write(new_content)

with open(target) as f:
    check = f.read()
if 'fake_midr' in check and 'Pura 90 Pro Max' in check:
    print("  [OK] cpuinfo patched")
else:
    print("  [FAIL] cpuinfo not patched!")
    sys.exit(1)

# ===== 2. 伪装 /sys/devices/soc0/machine =====
target2 = 'drivers/soc/qcom/socinfo.c'
print(f"[2/2] Patching {target2}...")

with open(target2) as f:
    content2 = f.read()

# 找到 socinfo_machine 函数
old_func = '''static const char *socinfo_machine(struct device *dev, unsigned int id)
{
\tint idx;

\tfor (idx = 0; idx < ARRAY_SIZE(soc_id); idx++) {
\t\tif (soc_id[idx].id == id)
\t\t\treturn soc_id[idx].name;
\t}

\treturn NULL;
}'''

new_soc_func = '''static const char *socinfo_machine(struct device *dev, unsigned int id)
{
\treturn "SCA-AL00";
}'''

if old_func in content2:
    content2 = content2.replace(old_func, new_soc_func)
    print("  [OK] socinfo patched (exact match)")
else:
    # tab vs spaces fallback
    pattern = r'static const char \*socinfo_machine$struct device \*dev, unsigned int id$\s*\{.*?\n\}'
    m = re.search(pattern, content2, re.DOTALL)
    if m:
        content2 = content2[:m.start()] + new_soc_func + content2[m.end():]
        print("  [OK] socinfo patched (regex)")
    else:
        print("  [WARN] socinfo_machine not found, skipping")

with open(target2, 'w') as f:
    f.write(content2)

# ===== 验证 =====
with open(target2) as f:
    check2 = f.read()
if 'SCA-AL00' in check2:
    print("  [OK] socinfo verified")
else:
    print("  [WARN] socinfo may not be applied")

print("\n=== All spoofing patches applied ===")
