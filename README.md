# 🚀 SJA1110 FRER - Simple & Working!

> **NXP SJA1110에서 FRER (Frame Replication) 완벽 구현**

## 🎯 사용할 파일 (딱 2개!)

```
binaries/
├── sja1110_switch_frer.bin    # FRER 활성화된 스위치 설정 (2,236 bytes)
└── sja1110_uc_frer.bin        # 마이크로컨트롤러 펌웨어 (320,280 bytes)
```

**이 2개 파일만 있으면 FRER 동작합니다!** 📦

## 📋 설치 방법 (3단계)

```bash
# 1. S32G274A-RDB2 보드에 펌웨어 업로드
scp binaries/sja1110_switch_frer.bin root@192.168.1.1:/lib/firmware/sja1110_switch.bin
scp binaries/sja1110_uc_frer.bin root@192.168.1.1:/lib/firmware/sja1110_uc.bin

# 2. 재부팅
ssh root@192.168.1.1 reboot

# 3. 성공 확인
ssh root@192.168.1.1 'dmesg | grep sja1110'
```

### ✅ 성공하면 이렇게 나옵니다:
```
sja1110 spi5.1: Uploading config...
sja1110 spi5.1: Configuration successful          # ← CRC 에러 없음!
sja1110 spi5.0: Upload successfully verified!
```

## 🔄 FRER 동작 방식

```
Port 4 (입력) → [SJA1110 FRER 엔진] → Port 2 (출력 A)
                                    → Port 3 (출력 B)
```

- **Port 4에 프레임 전송** → **Port 2, 3에서 동일한 프레임 2개** 나옴
- **R-TAG (0xF1C1)** 자동으로 추가되어 시퀀스 넘버링
- **IEEE 802.1CB 표준** 준수한 프레임 복제

## 🧪 FRER 테스트

```bash
# 두 출력 포트 모니터링
tcpdump -i eth2 -e -XX | grep "f1 c1"  # Port 2
tcpdump -i eth3 -e -XX | grep "f1 c1"  # Port 3

# Port 4로 테스트 프레임 전송 (패킷 생성기 사용)
# Port 2와 Port 3에서 동일한 프레임이 나오는지 확인!
```

## 🏆 왜 이게 동작하는가

- **✅ 정확한 CRC 알고리즘** - NXP 소스에서 찾은 정확한 구현
- **✅ LocalCRCfail 에러 없음** - CRC 검증 완벽 통과
- **✅ 진짜 UC 펌웨어** - GoldVIP 마이크로컨트롤러 코드 사용
- **✅ 올바른 FRER 설정** - CB_EN 활성화, 포트 올바르게 구성

## 🛠️ 해결한 문제들

| 문제 | 이전 | 이후 |
|------|------|------|
| CRC 에러 | `LocalCRCfail=1` | ✅ 에러 없음 |
| 펌웨어 로드 | 실패 | ✅ 성공 |
| FRER 동작 | 안됨 | ✅ 완벽 동작 |

## 📚 추가 정보

- **[HOW_TO_USE.md](HOW_TO_USE.md)** - 간단 사용법
- **[SUMMARY.md](SUMMARY.md)** - 프로젝트 전체 요약
- **[docs/](docs/)** - 기술적 세부사항

## 🐛 문제 해결

| 문제 | 해결방법 |
|------|----------|
| LocalCRCfail=1 | 우리 파일 사용 - CRC 수정됨! |
| 업로드 실패 | 경로 확인: `/lib/firmware/` |
| 복제 안됨 | 포트 링크 상태 확인 |

## 💻 레포지토리 구조

```
sja1110/
├── binaries/                  # 🎯 메인 파일 - 이것만 사용하세요!
│   ├── sja1110_switch_frer.bin     # 스위치 설정
│   └── sja1110_uc_frer.bin         # UC 펌웨어
│
├── source/                    # 구현 코드
├── docs/                      # 상세 문서
├── tools/                     # 도구들
└── HOW_TO_USE.md             # 간단 가이드
```

## 🌟 기술 스펙

- **플랫폼**: S32G274A-RDB2
- **스위치**: NXP SJA1110
- **표준**: IEEE 802.1CB-2017
- **복제**: Port 4 → Ports 2,3
- **R-TAG**: 0xF1C1
- **복구 윈도우**: 256 frames
- **타임아웃**: 1000ms

## 🎉 결론

**`/binaries/`의 2개 파일만 사용하면 FRER이 바로 동작합니다!**

더 이상 CRC 에러도 없고, 복잡한 설정도 필요 없습니다. 그냥 동작합니다. 🚀

---

**만든이**: SJA1110 FRER 팀
**저장소**: https://github.com/hwkim3330/sja1110
**상태**: 🟢 **프로덕션 레디**