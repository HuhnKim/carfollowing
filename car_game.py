import pygame
import sys
import os
import random
import time
import math  # 추가: 무한대 확인을 위한 math 모듈
from player_car import PlayerCar
from front_car import FrontCar

class CarGame:
    def __init__(self):
        pygame.init()
        self.width = 800
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("자동차 안전거리 교육 게임")
        
        # 폰트 설정
        self.setup_fonts()
        
        # 게임 변수
        self.clock = pygame.time.Clock()
        self.traveled_distance = 0  # 이동한 거리 (미터)
        
        # 도로 설정
        self.road_width = 400
        self.road_left = (self.width - self.road_width) // 2
        self.road_right = self.road_left + self.road_width
        
        # 차량 초기화
        self.player_car = PlayerCar(self.width // 2, self.height - 100)
        self.front_car = FrontCar(self.width // 2, 150)  # y 위치를 200에서 150으로 변경하여 더 위쪽에 배치
        
        # 거리 관련 변수
        self.car_distance = 250  # 초기 차량 간 실제 거리를 100m에서 250m로 증가
        self.min_car_distance = 8  # 최소 차량 간 거리 감소 (10 → 8)
        self.max_visual_distance = self.height * 0.7  # 화면에 표시할 최대 시각적 거리
        
        # 앞 차량의 운전 행동 패턴
        self.driving_modes = ["normal", "aggressive", "cautious"]
        self.current_driving_mode = "normal"
        self.driving_pattern_timer = 0
        self.mode_duration = random.randint(5000, 15000)  # 5~15초마다 운전 스타일 변경
        
        # 앞차 속도 변화 패턴 관련 변수
        self.speed_change_timer = 0
        self.speed_change_interval = random.randint(2000, 5000)  # 2~5초마다 속도 변경
        self.target_speed_factor = 1.0  # 목표 속도 계수
        
        # 게임 상태
        self.game_over = False
        self.crash_time = 0
        self.crash_count = 0  # 충돌 횟수 기록
        self.last_crash_time = 0  # 마지막 충돌 시간
        self.show_crash_effect = False  # 충돌 효과 표시 여부
        self.crash_effect_duration = 2000  # 충돌 효과 지속 시간 (2초)
        
        # 디버그 정보
        self.show_debug = False  # 디버그 정보 표시 여부
        
        # 시간 설정
        self.last_update_time = pygame.time.get_ticks()
    
    def setup_fonts(self):
        """폰트 설정을 별도 메서드로 분리"""
        # 여러 폰트 경로 시도
        font_paths = [
            os.path.join("fonts", "HANCOM GOTHIC REGULAR.ttf"),
            os.path.join("fonts", "NanumGothic.ttf"),
            os.path.join("fonts", "gulim.ttc"),  # Windows 기본 폰트
            os.path.join("fonts", "malgun.ttf")  # Windows 기본 폰트
        ]
        
        # 시스템 폰트 경로도 확인 (Windows)
        system_font_paths = [
            os.path.join(os.environ.get('WINDIR', ''), 'Fonts', 'malgun.ttf'),
            os.path.join(os.environ.get('WINDIR', ''), 'Fonts', 'gulim.ttc')
        ]
        
        font_paths.extend(system_font_paths)
        
        # 폰트 파일 존재 확인 및 로드
        self.font = None
        self.small_font = None
        
        for path in font_paths:
            if os.path.exists(path):
                try:
                    self.font = pygame.font.Font(path, 24)
                    self.small_font = pygame.font.Font(path, 16)
                    print(f"폰트 로드 성공: {path}")
                    break
                except Exception as e:
                    print(f"폰트 로드 실패: {path} - {e}")
        
        # 폰트를 찾지 못한 경우 기본 폰트 사용
        if self.font is None:
            print("한글 폰트를 찾지 못했습니다. 기본 폰트를 사용합니다.")
            self.font = pygame.font.SysFont(None, 24)
            self.small_font = pygame.font.SysFont(None, 16)
    
    def run(self):
        while not self.game_over:
            self.handle_events()
            
            # 게임 업데이트
            self.update()
            
            # 그리기
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)
            
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            # ESC 키로 종료
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            
            # D 키로 디버그 모드 전환
            if event.type == pygame.KEYDOWN and event.key == pygame.K_d:
                self.show_debug = not self.show_debug
                
            # R 키로 재시작
            if self.game_over and event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.__init__()  # 게임 재시작
                
            # 플레이어 차량 이벤트 처리
            if not self.game_over:
                self.player_car.handle_event(event)
                
    def update(self):
        """게임 상태 업데이트"""
        if self.game_over:
            return
        
        # 플레이어 차량 업데이트
        self.player_car.update(self.road_left, self.road_right)
        
        # 속도 값 안전 확인 (무한대 방지)
        self.player_car.speed = min(max(self.player_car.speed, self.player_car.min_speed), self.player_car.max_speed)
        self.player_car.target_speed = min(max(self.player_car.target_speed, self.player_car.min_speed), self.player_car.max_speed)
        
        # 앞 차량 업데이트
        self.front_car.update(self.road_left, self.road_right)
        
        # 앞차 속도 안전 확인 (무한대 방지)
        self.front_car.speed = min(max(self.front_car.speed, self.front_car.min_speed), self.front_car.max_speed)
        self.front_car.target_speed = min(max(self.front_car.target_speed, self.front_car.min_speed), self.front_car.max_speed)
        
        # 충돌 후 회복 상태에서는 속도 패턴을 적용하지 않음
        if not hasattr(self, 'collision_recovery') or not self.collision_recovery:
            # 앞차 속도 변화 패턴 업데이트
            self.update_speed_change_pattern()
            
            # 운전 패턴 업데이트
            self.update_driving_pattern()
            
            # 앞 차량 행동 조정 - 안전 거리 기반 로직 제거하고 단순화
            self.adjust_front_car_behavior()
        
        # 차량 간 거리 업데이트 (속도차이에 따른 거리 변화)
        distance_change = (self.front_car.speed - self.player_car.speed) * 1/60  # 초당 거리 변화
        self.car_distance += distance_change
        
        # 최소 거리 제한
        self.car_distance = max(self.car_distance, self.min_car_distance)
        
        # 충돌 검사
        self.check_collision()
        
        # 충돌 효과 업데이트
        current_time = pygame.time.get_ticks()
        if self.show_crash_effect and current_time - self.last_crash_time > self.crash_effect_duration:
            self.show_crash_effect = False
        
        # 이동 거리 누적 - 무한대 방지
        if not math.isinf(self.player_car.speed) and not math.isnan(self.player_car.speed):
            self.traveled_distance += self.player_car.speed * 1/60  # 초당 거리 누적
        
        # 거리에 따른 앞 차량의 시각적 위치 계산
        front_car_visual_y = self._calculate_front_car_visual_position()
        
        # 원근감에 따른 앞 차량의 크기 조정
        size_ratio = self._calculate_size_ratio()
        self.front_car.set_visual_size(size_ratio)
        
        # 앞 차량의 시각적 위치 업데이트
        self.front_car.y = front_car_visual_y
    
    def update_speed_change_pattern(self):
        """앞차의 속도 변화 패턴을 관리"""
        # 속도 변화 타이머 업데이트
        self.speed_change_timer += 1/60 * 1000  # 밀리초 단위로 변환
        
        # 속도 변화 간격에 도달하면 새로운 목표 속도 설정
        if self.speed_change_timer >= self.speed_change_interval:
            self.speed_change_timer = 0
            
            # 운전 모드에 따른 속도 변화 간격 설정
            if self.current_driving_mode == "aggressive":
                self.speed_change_interval = random.randint(2000, 4000)  # 2~4초 (1.5~3초 → 2~4초)
            elif self.current_driving_mode == "cautious":
                self.speed_change_interval = random.randint(5000, 8000)  # 5~8초 (변경 없음)
            else:  # normal
                self.speed_change_interval = random.randint(3000, 6000)  # 3~6초 (3~5초 → 3~6초)
            
            # 현재 속도를 기준으로 새로운 목표 속도 설정
            base_speed = self.front_car.speed
            
            # 운전 모드에 따른 속도 변화 특성 (변화폭 축소)
            if self.current_driving_mode == "aggressive":
                # 공격적 운전: 약간 빠른 속도 변화
                if random.random() < 0.15:  # 15% 확률로 조금 더 큰 변화
                    # 급가속 또는 급감속 (변화폭 축소)
                    if random.random() < 0.5:  # 급가속
                        target_factor = random.uniform(1.1, 1.2)  # 10~20% 속도 변화 (1.3~1.5 → 1.1~1.2)
                    else:  # 급감속
                        target_factor = random.uniform(0.7, 0.85)  # 15~30% 속도 변화 (0.5~0.7 → 0.7~0.85)
                else:
                    # 일반적인 공격적 패턴 (변화폭 축소)
                    target_factor = random.uniform(0.9, 1.15)  # 10~15% 속도 변화 (0.8~1.3 → 0.9~1.15)
                
                # 플레이어 차량 추월 시도 (20% 확률)
                if random.random() < 0.2 and self.car_distance > 50:
                    player_based_factor = self.player_car.speed / base_speed * 1.05  # 5% 더 빠르게 (1.1 → 1.05)
                    target_factor = max(target_factor, player_based_factor)
            
            elif self.current_driving_mode == "cautious":
                # 조심스러운 운전: 매우 점진적인 속도 변화
                target_factor = random.uniform(0.95, 1.03)  # 더 작은 폭 (0.9~1.05 → 0.95~1.03)
                
                # 안전거리 확보를 위한 속도 조절
                player_speed_kph = self.player_car.speed * 3.6  # m/s에서 km/h로 변환
                safe_speed_factor = 0.95  # 플레이어보다 약간 느리게 (0.9 → 0.95)
                
                # 거리가 가까우면 더 느리게
                if self.car_distance < 100:
                    safe_speed_factor = 0.9  # 더 높게 설정 (0.8 → 0.9)
                
                # 플레이어 속도 기반 목표 설정 (조심스러운 추종)
                player_based_target = self.player_car.speed * safe_speed_factor
                player_weight = 0.7  # 플레이어 속도에 대한 가중치
                
                # 플레이어 속도와 랜덤 요소를 조합
                target_speed_from_player = player_based_target
                target_speed_from_random = base_speed * target_factor
                
                # 가중 평균 계산
                target_speed = (target_speed_from_player * player_weight + 
                               target_speed_from_random * (1 - player_weight))
                
                # 최종 목표 속도 계수 계산
                target_factor = target_speed / base_speed if base_speed > 0 else 1.0
            
            else:  # normal
                # 일반 운전: 안정적인 속도 변화
                target_factor = random.uniform(0.9, 1.1)  # 더 작은 폭 (0.85~1.15 → 0.9~1.1)
                
                # 가끔 플레이어 속도에 맞추기 (40% 확률)
                if random.random() < 0.4:
                    # 플레이어와 비슷한 속도로 조정하되 약간의 변동성 추가
                    player_based_target = self.player_car.speed * random.uniform(0.95, 1.03)  # 더 작은 폭 (0.9~1.05 → 0.95~1.03)
                    random_based_target = base_speed * target_factor
                    
                    # 두 요소를 혼합
                    mix_ratio = random.uniform(0.4, 0.6)  # 혼합 비율 안정화 (0.3~0.7 → 0.4~0.6)
                    target_speed = (player_based_target * mix_ratio + 
                                  random_based_target * (1 - mix_ratio))
                    
                    target_factor = target_speed / base_speed if base_speed > 0 else 1.0
                
                # 교통 흐름 시뮬레이션 (주기적으로 속도 감소 후 회복)
                if random.random() < 0.1:  # 10% 확률
                    # 패턴 시작: 감속 후 점진적 회복
                    self.traffic_flow_active = True
                    self.traffic_flow_phase = "slowdown"
                    self.traffic_flow_timer = 0
                    self.traffic_flow_initial_speed = base_speed
                    target_factor = random.uniform(0.7, 0.85)  # 더 높게 설정 (0.6~0.8 → 0.7~0.85)
            
            # 목표 속도 제한 (최대/최소 속도 범위 내에서 설정)
            target_speed = base_speed * target_factor
            
            # 속도 변화가 너무 급격하지 않도록 제한
            max_change = 15  # 최대 속도 변화를 15km/h로 제한
            if abs(target_speed - base_speed) > max_change:
                if target_speed > base_speed:
                    target_speed = base_speed + max_change
                else:
                    target_speed = base_speed - max_change
            
            target_speed = min(max(target_speed, self.front_car.min_speed), self.front_car.max_speed)
            self.front_car.target_speed = target_speed
            
            # 도로 상태에 따른 무작위 속도 변화 (요철, 커브 등)
            if random.random() < 0.05:  # 5% 확률
                # 일시적인 속도 변화 (커브, 장애물 등)
                self.road_condition_active = True
                self.road_condition_timer = 0
                self.road_condition_duration = random.uniform(1.0, 3.0)  # 1~3초
                self.road_condition_factor = random.uniform(0.9, 1.05)  # 변화폭 축소 (0.85~1.1 → 0.9~1.05)
        
        # 교통 흐름 패턴 처리 (감속 후 점진적 회복)
        if hasattr(self, 'traffic_flow_active') and self.traffic_flow_active:
            self.traffic_flow_timer += 1/60  # 초 단위 타이머
            
            if self.traffic_flow_phase == "slowdown" and self.traffic_flow_timer > 2.0:
                # 감속 후 회복 단계로 전환
                self.traffic_flow_phase = "recovery"
                self.traffic_flow_timer = 0
            
            elif self.traffic_flow_phase == "recovery":
                # 점진적 회복 (5초에 걸쳐 원래 속도로)
                if self.traffic_flow_timer > 5.0:
                    self.traffic_flow_active = False
                else:
                    # 회복 비율 계산 (0에서 1 사이로 증가)
                    recovery_ratio = self.traffic_flow_timer / 5.0
                    target_speed = (self.traffic_flow_initial_speed * 0.8 +  # 더 높게 설정 (0.7 → 0.8)
                                  recovery_ratio * (self.traffic_flow_initial_speed * 0.2))  # 더 작게 설정 (0.3 → 0.2)
                    self.front_car.target_speed = target_speed
        
        # 도로 상태에 따른 일시적 속도 변화
        if hasattr(self, 'road_condition_active') and self.road_condition_active:
            self.road_condition_timer += 1/60
            
            if self.road_condition_timer > self.road_condition_duration:
                self.road_condition_active = False
            else:
                # 도로 상태로 인한 일시적 속도 조정 (부드럽게)
                speed_adjust = (self.road_condition_factor - 1.0) * 0.5  # 절반의 효과만 적용
                adjusted_factor = 1.0 + speed_adjust
                self.front_car.speed = self.front_car.speed * adjusted_factor
        
        # 현재 속도를 목표 속도에 서서히 접근시킴
        speed_diff = self.front_car.target_speed - self.front_car.speed
        if abs(speed_diff) > 0.1:  # 0.1 m/s 이상 차이가 있을 때만 조정
            # 운전 모드에 따른 가속/감속 비율 조정 (더 부드럽게)
            if self.current_driving_mode == "aggressive":
                adjustment_rate = 0.5 * 1/60  # 중간 속도 변화 (0.8 → 0.5)
            elif self.current_driving_mode == "cautious":
                adjustment_rate = 0.25 * 1/60  # 더 느린 속도 변화 (0.3 → 0.25)
            else:  # normal
                adjustment_rate = 0.35 * 1/60  # 중간 속도 변화 (0.5 → 0.35)
                
            # 가속과 감속의 비율 차별화 (실제 차량처럼)
            if speed_diff > 0:  # 가속
                # 점진적 가속 구현
                accel_factor = min(1.0, abs(speed_diff) / 10)  # 속도 차이가 클수록 더 빠르게 가속
                self.front_car.speed += speed_diff * adjustment_rate * accel_factor
            else:  # 감속
                # 점진적 감속 구현
                decel_factor = min(1.0, abs(speed_diff) / 8)  # 속도 차이가 클수록 더 빠르게 감속
                self.front_car.speed += speed_diff * (adjustment_rate * 1.1) * decel_factor  # 감속은 약간 빠르게 (1.2 → 1.1)
    
    def update_driving_pattern(self):
        """앞 차량의 운전 패턴을 주기적으로 변경"""
        self.driving_pattern_timer += 1/60  # 60fps 기준
        
        # 패턴 변경 시간이 되면 새 패턴 설정
        if self.driving_pattern_timer >= self.mode_duration / 1000:
            self.driving_pattern_timer = 0
            
            # 다음 패턴 변경까지의 시간 (5초~15초 사이 랜덤)
            self.mode_duration = random.randint(5000, 15000)
            
            # 운전 모드 랜덤 선택 (확률: 일반 50%, 공격적 30%, 조심스러운 20%)
            self.current_driving_mode = random.choices(self.driving_modes, [50, 30, 20], k=1)[0]
    
    def adjust_front_car_behavior(self):
        """앞 차량 행동 조정 (단순화된 버전)"""
        # 운전 스타일에 따른 행동 조정
        if self.current_driving_mode == "aggressive":
            # 공격적 운전 스타일 - 급제동, 갑작스러운 가속, 지그재그 운전
            
            # 급제동 확률 (10%)
            if random.random() < 0.005:  # 프레임 당 확률 (60fps 기준 약 1/3초에 한번)
                self.front_car.apply_brake()
                self.sudden_brake_active = True
                self.sudden_brake_timer = 0
            
            # 급제동 해제 (0.5~1초 지속)
            if hasattr(self, 'sudden_brake_active') and self.sudden_brake_active:
                self.sudden_brake_timer += 1/60
                if self.sudden_brake_timer > random.uniform(0.5, 1.0):
                    self.front_car.release_brake()
                    self.sudden_brake_active = False
            
            # 급가속 확률 (8%)
            if not hasattr(self, 'sudden_brake_active') or not self.sudden_brake_active:
                if random.random() < 0.004:
                    boost_factor = random.uniform(1.1, 1.3)
                    self.front_car.speed = min(self.front_car.speed * boost_factor, self.front_car.max_speed)
            
            # 차선 이탈 확률 (차선 내에서 좌우 이동)
            if random.random() < 0.01:
                lateral_shift = random.uniform(-20, 20)
                self.front_car.x = max(self.road_left + 30, min(self.road_right - 30, self.front_car.x + lateral_shift))
        
        elif self.current_driving_mode == "cautious":
            # 조심스러운 운전 스타일 - 천천히 가속/감속
            
            # 차선 중앙 유지 경향
            center_x = (self.road_left + self.road_right) / 2
            self.front_car.x += (center_x - self.front_car.x) * 0.02  # 부드럽게 중앙으로 이동
        
        else:  # normal
            # 일반 운전 스타일 - 균형 잡힌 가속/감속
            
            # 차선 내에서 약간의 자연스러운 움직임
            if random.random() < 0.005:
                drift = random.uniform(-10, 10)
                self.front_car.x = max(self.road_left + 30, min(self.road_right - 30, self.front_car.x + drift))
        
        # 앞 차량이 도로 경계를 넘지 않도록 함
        self.front_car.x = max(self.road_left + 30, min(self.road_right - 30, self.front_car.x))
    
    def _calculate_front_car_visual_position(self):
        """거리에 따른 앞 차량의 시각적 위치 계산"""
        # 화면 내에서 두 차량 사이의 시각적 최대 거리
        visual_distance = (self.height - 200) * 0.8
        
        # 충돌 회복 중일 때는 더 빠르게 분리되도록 시각적 거리 확대
        if hasattr(self, 'collision_recovery') and self.collision_recovery:
            distance_ratio = min(1.0, (self.car_distance / 250))  # 거리 계수를 더 민감하게 설정 (350 → 250)
            front_car_y = self.player_car.y - distance_ratio * visual_distance * 1.5  # 시각적 거리를 50% 확대
        else:
            # 일반 상태에서는 기존 로직 사용
            distance_ratio = min(1.0, self.car_distance / 350)
            front_car_y = self.player_car.y - distance_ratio * visual_distance
        
        # 최소/최대 제한
        min_y = 100  # 화면 상단 제한
        max_y = self.player_car.y - 80  # 플레이어 차량에 너무 가깝지 않도록
        
        return max(min_y, min(front_car_y, max_y))
    
    def _calculate_size_ratio(self):
        """거리에 따른 앞 차량의 크기 비율 계산"""
        # 거리에 따른 크기 조정 (멀면 작게, 가까우면 크게) - 더 극적인 크기 변화
        perspective_factor = 0.75  # 원근감 계수 증가 (0.6 → 0.75)
        distance_ratio = min(1.0, self.car_distance / 350)  # 최대 거리 증가 (300 → 350)
        size_ratio = 1.0 - distance_ratio * perspective_factor
        
        return size_ratio
    
    def check_collision(self):
        """차량 간 충돌 확인 - 사각형 겹침 로직"""
        # 각 차량의 사각형 영역 계산
        player_rect = pygame.Rect(
            self.player_car.x - self.player_car.width // 2,
            self.player_car.y - self.player_car.height // 2,
            self.player_car.width,
            self.player_car.height
        )
        
        front_rect = pygame.Rect(
            self.front_car.x - self.front_car.width // 2,
            self.front_car.y - self.front_car.height // 2,
            self.front_car.width,
            self.front_car.height
        )
        
        # 사각형이 겹치는지 확인
        if player_rect.colliderect(front_rect):
            current_time = pygame.time.get_ticks()
            # 충돌 간격이 1초 이상일 때만 새로운 충돌로 카운트 (연속 충돌 방지)
            if current_time - self.last_crash_time > 1000:
                self.crash_count += 1
                self.last_crash_time = current_time
                self.show_crash_effect = True
                print(f"충돌 발생! (총 {self.crash_count}회)")
                
                # 충돌 상태 설정 - 충돌 후 회복 시간 관리
                self.collision_recovery = True
                self.collision_recovery_timer = 0
                self.collision_recovery_duration = 2.0  # 충돌 후 회복에 걸리는 시간(초)
                
                # 충돌 직후 앞 차의 y 위치를 강제로 조정하여 사각형이 겹치지 않도록 함
                # 플레이어 차 위쪽으로 최소한의 간격을 확보
                self.front_car.y = self.player_car.y - self.player_car.height - 20
            
            # 차량 사이에 최소 거리 유지 (밀착 방지)
            self.car_distance = self.min_car_distance + 50  # 더 큰 간격으로 분리 (20 → 50)
            
            # 충돌 후 앞 차 속도 증가 (빠른 분리를 위함) - 변화폭 축소
            accel_factor = random.uniform(1.2, 1.4)  # 20~40% 가속 (1.5~2.0 → 1.2~1.4)
            new_speed = min(self.front_car.max_speed, self.front_car.speed * accel_factor)
            # 최소 속도 보장 (플레이어보다 빠르게)
            min_escape_speed = self.player_car.speed * 1.3  # 플레이어보다 30% 빠르게 (1.5 → 1.3)
            self.front_car.speed = max(new_speed, min_escape_speed)
            
            # 플레이어 속도 감소 (충돌 효과)
            self.player_car.speed = max(self.player_car.min_speed, self.player_car.speed * 0.8)  # 속도 감소 조정 (0.7 → 0.8)
            
            # 앞 차가 좌우로 약간 이동하여 충돌 위치에서 벗어나도록 함
            if self.player_car.x > self.front_car.x:
                # 플레이어가 앞 차의 오른쪽에 있으면 앞 차는 왼쪽으로 이동
                new_x = max(self.road_left + 40, self.front_car.x - random.uniform(20, 35))  # 이동 거리 축소 (30~50 → 20~35)
                self.front_car.x = new_x
            else:
                # 플레이어가 앞 차의 왼쪽에 있으면 앞 차는 오른쪽으로 이동
                new_x = min(self.road_right - 40, self.front_car.x + random.uniform(20, 35))  # 이동 거리 축소 (30~50 → 20~35)
                self.front_car.x = new_x
            
            # 강제로 충돌 상태에서 벗어나기 위해 차량 간 거리를 시각적으로도 즉시 반영
            front_car_visual_y = self._calculate_front_car_visual_position()
            self.front_car.y = front_car_visual_y
        
        # 충돌 후 회복 처리
        if hasattr(self, 'collision_recovery') and self.collision_recovery:
            self.collision_recovery_timer += 1/60  # 60fps 기준
            
            # 회복 시간 동안 앞 차는 플레이어보다 빠르게 유지
            min_speed = self.player_car.speed * 1.2  # 플레이어보다 20% 빠르게 (1.3 → 1.2)
            self.front_car.speed = max(self.front_car.speed, min_speed)
            
            # 충돌 중에는 강제로 차량 사이 거리를 확보
            if player_rect.colliderect(front_rect):
                # y축 방향으로 강제 분리
                self.front_car.y = self.player_car.y - self.player_car.height - 20
                # 좌우 방향으로 추가 이동
                if self.player_car.x > self.front_car.x:
                    self.front_car.x = max(self.road_left + 40, self.front_car.x - 10)
                else:
                    self.front_car.x = min(self.road_right - 40, self.front_car.x + 10)
            
            # 회복 시간이 끝나면 정상 상태로 복귀
            if self.collision_recovery_timer >= self.collision_recovery_duration:
                self.collision_recovery = False
                
    def draw(self):
        """게임 화면 그리기"""
        # 배경
        self.screen.fill((100, 180, 100))  # 연한 초록색 (잔디)
        
        # 도로 그리기
        pygame.draw.rect(self.screen, (80, 80, 80), 
                        (self.road_left, 0, self.road_width, self.height))
        
        # 도로 경계선
        pygame.draw.line(self.screen, (255, 255, 255), 
                         (self.road_left, 0), (self.road_left, self.height), 5)
        pygame.draw.line(self.screen, (255, 255, 255), 
                         (self.road_right, 0), (self.road_right, self.height), 5)
        
        # 중앙선 그리기 (점선) - 무한대 방지
        center_x = self.width // 2
        line_length = 30
        gap_length = 20
        # 무한대 값 방지
        safe_distance = min(self.traveled_distance, 1000000000)  # 너무 큰 값 제한
        
        # 플레이어 속도에 비례한 이동 속도 계수 (자동차 속도에 따라 중앙선이 더 빠르게 움직임)
        # 기준 속도를 60km/h로 설정하고, 그 속도에서는 2배 속도로 이동
        base_speed = 60  # 기준 속도 (km/h)
        base_factor = 2.0  # 기준 계수
        speed_ratio = self.player_car.speed / base_speed  # 현재 속도와 기준 속도의 비율
        speed_factor = base_factor * speed_ratio  # 속도에 비례한 계수
        
        # 최소 및 최대 계수 제한
        speed_factor = max(1.0, min(3.0, speed_factor))  # 최소 1배, 최대 5배 속도
        
        offset_distance = safe_distance * speed_factor
        
        for y in range(0, self.height, line_length + gap_length):
            offset = int(offset_distance) % (line_length + gap_length)
            line_y = y - offset
            if line_y >= 0 and line_y < self.height - line_length:
                pygame.draw.line(self.screen, (255, 255, 0), 
                                (center_x, line_y), 
                                (center_x, line_y + line_length), 2)
        
        # 차량 그리기
        self.front_car.draw(self.screen)
        self.player_car.draw(self.screen)
        
        # 충돌 효과 그리기
        if self.show_crash_effect:
            self.draw_crash_effect()
        
        # 게임 정보 표시
        self.draw_game_info()
        
        # 디버그 정보 표시
        if self.show_debug:
            self.draw_debug_info()
            
    def draw_crash_effect(self):
        """충돌 효과 그리기"""
        # 충돌 위치 (플레이어 차량의 전방)
        crash_x = self.player_car.x
        crash_y = self.player_car.y - self.player_car.height // 2
        
        # 각 차량의 사각형 영역 시각화
        player_rect = pygame.Rect(
            self.player_car.x - self.player_car.width // 2,
            self.player_car.y - self.player_car.height // 2,
            self.player_car.width,
            self.player_car.height
        )
        
        front_rect = pygame.Rect(
            self.front_car.x - self.front_car.width // 2,
            self.front_car.y - self.front_car.height // 2,
            self.front_car.width,
            self.front_car.height
        )
        
        # 충돌 사각형 강조 표시
        pygame.draw.rect(self.screen, (255, 255, 0), player_rect, 2)
        pygame.draw.rect(self.screen, (255, 255, 0), front_rect, 2)
        
        # 충돌 영역 표시 (겹치는 부분)
        intersection = player_rect.clip(front_rect)
        if not intersection.width == 0 and not intersection.height == 0:
            # 겹치는 영역을 빨간색으로 강조
            collision_surface = pygame.Surface((intersection.width, intersection.height), pygame.SRCALPHA)
            collision_surface.fill((255, 0, 0, 150))  # 반투명 빨간색
            self.screen.blit(collision_surface, intersection.topleft)
        
        # 화면 전체에 반투명 붉은색 오버레이
        flash_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        alpha = max(0, 150 - (pygame.time.get_ticks() - self.last_crash_time) / 5)  # 시간이 지날수록 투명해짐
        flash_surface.fill((255, 0, 0, alpha))
        self.screen.blit(flash_surface, (0, 0))
        
        # 충돌 지점에 효과 그리기
        effect_size = 40
        pygame.draw.circle(self.screen, (255, 255, 0), (int(crash_x), int(crash_y)), effect_size, 3)
        pygame.draw.circle(self.screen, (255, 150, 0), (int(crash_x), int(crash_y)), effect_size // 2, 2)
        
        # 충돌 텍스트
        crash_text = f"충돌! ({self.crash_count}회)"
        text_surface = self.font.render(crash_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(self.width // 2, 50))
        
        # 텍스트 배경
        bg_rect = text_rect.inflate(20, 10)
        pygame.draw.rect(self.screen, (200, 0, 0), bg_rect)
        pygame.draw.rect(self.screen, (255, 255, 255), bg_rect, 2)
        
        # 텍스트 그리기
        self.screen.blit(text_surface, text_rect)
    
    def draw_game_info(self):
        """게임 정보 표시"""
        # 플레이어 속도 표시
        speed_text = f"속도: {self.player_car.speed:.1f} km/h"
        speed_surface = self.font.render(speed_text, True, (255, 255, 255))
        self.screen.blit(speed_surface, (10, 10))
        
        # 이동 거리 표시
        distance_text = f"이동 거리: {self.traveled_distance:.1f} m"
        distance_surface = self.font.render(distance_text, True, (255, 255, 255))
        self.screen.blit(distance_surface, (10, 40))
        
        # 앞 차와의 거리
        distance_text = f"앞 차와의 거리: {self.car_distance:.1f} m"
        distance_surface = self.font.render(distance_text, True, (255, 255, 255))
        self.screen.blit(distance_surface, (10, 70))
        
        # 앞 차 속도 표시
        front_speed_text = f"앞 차 속도: {self.front_car.speed:.1f} km/h"
        front_speed_surface = self.font.render(front_speed_text, True, (255, 255, 255))
        self.screen.blit(front_speed_surface, (10, 100))
        
        # 충돌 횟수 표시
        crash_text = f"충돌 횟수: {self.crash_count}"
        crash_surface = self.font.render(crash_text, True, (255, 255, 255))
        self.screen.blit(crash_surface, (10, 130))
        
        # 조작 안내
        controls_text = "방향키: ↑(가속) ↓(감속) ←→(좌우이동) | R: 재시작 | D: 디버그 | ESC: 종료"
        controls_surface = self.small_font.render(controls_text, True, (255, 255, 255))
        self.screen.blit(controls_surface, (10, self.height - 30))
    
    def draw_debug_info(self):
        """디버그 정보 표시"""
        if not self.show_debug:
            return
            
        debug_info = [
            f"플레이어 속도: {self.player_car.speed:.1f} km/h",
            f"앞 차량 속도: {self.front_car.speed:.1f} km/h",
            f"차량 간 거리: {self.car_distance:.1f} m",
            f"이동 거리: {self.traveled_distance:.1f} m",
            f"운전 모드: {self.current_driving_mode}"
        ]
        
        y_offset = 10
        for info in debug_info:
            text = self.small_font.render(info, True, (255, 255, 255))
            text_rect = text.get_rect(topleft=(10, y_offset))
            # 텍스트 그림자 효과
            shadow = self.small_font.render(info, True, (0, 0, 0))
            shadow_rect = shadow.get_rect(topleft=(text_rect.x + 1, text_rect.y + 1))
            self.screen.blit(shadow, shadow_rect)
            self.screen.blit(text, text_rect)
            y_offset += 25

if __name__ == "__main__":
    game = CarGame()
    game.run() 