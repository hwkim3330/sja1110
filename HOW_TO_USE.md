# 🚀 SJA1110 FRER 사용법 (초간단)

## 🎯 핵심 파일 2개만 있으면 됨!

```
binaries/
├── sja1110_switch_frer.bin    # FRER 활성화된 스위치 설정 (2,236 bytes)
└── sja1110_uc_frer.bin        # 마이크로컨트롤러 펌웨어 (320,280 bytes)
```

## 📋 설치 방법 (3단계)

### 1단계: 파일 업로드
```bash
scp binaries/sja1110_switch_frer.bin root@192.168.1.1:/lib/firmware/sja1110_switch.bin
scp binaries/sja1110_uc_frer.bin root@192.168.1.1:/lib/firmware/sja1110_uc.bin
```

### 2단계: 재부팅
```bash
ssh root@192.168.1.1 reboot
```

### 3단계: 확인
```bash
ssh root@192.168.1.1 'dmesg | grep sja1110'
```

## ✅ 성공 확인

이런 메시지가 나오면 성공:
```
sja1110 spi5.1: Uploading config...
sja1110 spi5.1: Configuration successful
sja1110 spi5.0: Upload successfully verified!
```

## 🔄 FRER 동작 방식

```
Port 4 (입력) → [SJA1110 FRER] → Port 2 (출력 A)
                                → Port 3 (출력 B)
```

- **Port 4에 프레임 보내면** → Port 2와 Port 3에서 동일한 프레임 2개 나옴
- **R-TAG (0xF1C1)** 자동으로 추가됨

## 🧪 테스트 방법

```bash
# Port 2에서 모니터링
tcpdump -i eth2 -e -XX | grep "f1 c1"

# Port 3에서 모니터링
tcpdump -i eth3 -e -XX | grep "f1 c1"

# Port 4로 패킷 전송 (패킷 생성기 사용)
```

## ❌ 에러 시 체크사항

1. **LocalCRCfail=1** → 우리 파일 사용하면 해결됨
2. **파일 업로드 실패** → 경로 확인: `/lib/firmware/`
3. **FRER 동작 안함** → 포트 링크 상태 확인

## 🎉 그게 전부!

이 2개 파일만 업로드하면 FRER이 바로 동작합니다!

---

**간단 요약**:
1. 2개 파일 업로드
2. 재부팅
3. FRER 동작 ✅