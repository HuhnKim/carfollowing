import pygame
import random
import time

class FrontCar:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 60
        self.height = 100
        self.orig_width = 60  # 원래 크기 저장
        self.orig_height = 100  # 원래 크기 저장
        self.color = (0, 0, 200)  # 파란색
        self.visual_size = 1.0  # 시각적 크기 비율
        
        # 속도 관련 변수 (km/h)
        self.min_speed = 80  # 최소 속도 (30 → 80)
        self.max_speed = 160  # 최대 속도 (180 → 160)
        self.cruise_speed = 120  # 평균 주행 속도
        self.speed = random.uniform(100, 140)  # 초기 속도를 100~140km/h 사이로 설정 (110~130 → 100~140)
        self.target_speed = self.speed
        self.prev_speed = self.speed  # 이전 속도 저장 (감속 감지용)
        
        # 이징(easing) 관련 변수
        self.speed_smoothing = 0.8  # 속도 변화 부드러움 계수
        self.is_speed_transitioning = False  # 속도 전환 중인지 여부
        self.speed_transition_timer = 0  # 속도 전환 타이머
        self.speed_transition_duration = 0  # 속도 전환 지속 시간
        self.speed_transition_start = self.speed  # 전환 시작 속도
        self.speed_transition_type = "linear"  # 전환 유형 (linear, ease-in, ease-out, ease-in-out)
        
        # 브레이크 관련 변수
        self.is_braking = False
        self.brake_time = 0
        self.brake_duration = 0
        self.brake_intensity = 0  # 0: 브레이크 없음, 1: 약한 브레이크, 2: 강한 브레이크
        self.next_brake_time = random.uniform(1.5, 3.0)  # 더 자주 브레이크를 밟도록 변경 (2-4 → 1.5-3.0)
        self.brake_timer = 0
        
        # 브레이크 후효과 추가
        self.brake_afterglow = False  # 브레이크 후효과 활성화 여부
        self.afterglow_time = 0  # 브레이크 후효과 시간
        self.afterglow_duration = 0  # 브레이크 후효과 지속 시간
        
        # 브레이크등 추가 변수
        self.brake_lights_on = False  # 브레이크등 상태
        self.is_decelerating = False  # 감속 중인지 여부
        self.deceleration_threshold = 1.0  # 감속 감지 임계값 (km/h)
        
        # 좌우 움직임 관련 변수
        self.lane_change_timer = 0
        self.lane_change_interval = random.uniform(1.0, 2.5)  # 더 자주 차선 변경 (1.5-3 → 1.0-2.5)
        self.target_x = x + random.uniform(-30, 30)  # 초기에 랜덤한 위치로 설정
        self.move_speed = 3.0  # 좌우 이동 속도 크게 증가 (2.0 → 3.0)
        self.max_lane_deviation = 40  # 중앙에서 최대 이탈 거리
        
        # 속도 변화 랜덤화 (갑작스러운 속도 변화 추가)
        self.speed_change_timer = 0
        self.next_speed_change = random.uniform(3, 6)  # 더 자주 속도 변화 발생 (4-8 → 3-6)
    
    def set_visual_size(self, size_ratio):
        """원근감을 위한 시각적 크기 설정"""
        self.visual_size = max(0.3, min(1.0, size_ratio))  # 너무 작아지지 않도록 제한
        self.width = int(self.orig_width * self.visual_size)
        self.height = int(self.orig_height * self.visual_size)
    
    def update(self, road_left, road_right):
        """앞 차량 상태 업데이트"""
        # 이전 속도 저장 (감속 감지용)
        self.prev_speed = self.speed
        
        # 브레이크 타이머 증가
        self.brake_timer += 1/60  # 60fps 기준
        
        # 속도 변화 타이머 증가
        self.speed_change_timer += 1/60
        
        # 랜덤 속도 변화 적용 (평소 운전 패턴)
        if not self.is_braking and self.speed_change_timer >= self.next_speed_change:
            self.speed_change_timer = 0
            self.next_speed_change = random.uniform(2.5, 5.5)  # 더 자주 속도 변화 발생 (3-7 → 2.5-5.5)
            
            # 속도 변화 - 기본적으로 순항 속도(120) 주변에서 변동
            cruise_deviation = random.uniform(-15, 15)  # 순항 속도 기준 ±15km/h 변동
            new_target_speed = max(self.min_speed, min(self.max_speed, self.cruise_speed + cruise_deviation))
            
            # 새로운 목표 속도를 향해 이징(easing) 전환 시작
            if abs(new_target_speed - self.target_speed) > 3:  # 작은 변화는 무시
                # 브레이크 없는 가속은 더 빠르게 (0.6~1.2초)
                if new_target_speed > self.speed:
                    speed_diff = abs(new_target_speed - self.speed)
                    duration = max(0.6, min(1.2, 0.6 + (speed_diff / 60) * 0.6))
                    self.start_speed_transition(new_target_speed, "ease-in-out", duration)
                else:
                    # 감속은 조금 더 길게 (상대적으로)
                    self.start_speed_transition(new_target_speed, "ease-in-out")
            
            # 큰 속도 변화일 경우 브레이크 효과 추가 (100km/h 이상에서만)
            if new_target_speed < self.speed - 5 and self.speed >= 100:  # 100km/h 이상에서만 브레이크 적용
                self.apply_brake()
        
        # 브레이크 상태가 아니고 다음 브레이크 시간이 됐을 때 (100km/h 이상에서만)
        if not self.is_braking and not self.brake_afterglow and self.brake_timer >= self.next_brake_time and self.speed >= 100:
            self.apply_brake()
        
        # 브레이크 중인 경우
        if self.is_braking:
            self.brake_time += 1/60  # 60fps 기준
            
            # 브레이크 세기에 따라 속도 감소
            if self.brake_intensity == 1:  # 약한 브레이크
                target_brake_speed = max(self.min_speed, self.speed - 60)  # 약한 브레이크 감속 효과 (60km/h 감소)
                self.start_speed_transition(target_brake_speed, "ease-out", 2)
            else:  # 강한 브레이크
                target_brake_speed = max(self.min_speed, self.speed - 150)  # 강한 브레이크 감속 효과 (150km/h 감소)
                self.start_speed_transition(target_brake_speed, "ease-out", 4)
            
            # 브레이크 등 켜기
            self.brake_lights_on = True
            
            # 브레이크 시간이 끝났을 때
            if self.brake_time >= self.brake_duration:
                self.release_brake()
                # 브레이크 후효과 활성화
                self.brake_afterglow = True
                self.afterglow_time = 0
                self.afterglow_duration = random.uniform(1.5, 2.5)  # 후효과 지속 시간 단축 (2.0-3.5 → 1.5-2.5)
        
        # 브레이크 후효과 업데이트
        elif self.brake_afterglow:
            self.afterglow_time += 1/60  # 60fps 기준
            
            # 후효과 시간이 끝났을 때
            if self.afterglow_time >= self.afterglow_duration:
                self.brake_afterglow = False
                self.brake_timer = 0
                self.next_brake_time = random.uniform(1.0, 2.5)  # 다음 브레이크까지 시간 단축 (1.5-3.0 → 1.0-2.5)
                
                # 감속 중이 아니면 브레이크등 끄기
                if not self.is_decelerating:
                    self.brake_lights_on = False
                    
                # 브레이크 후 순항 속도로 복귀하는 경향 추가
                if self.speed < self.cruise_speed - 20:
                    return_target = min(self.cruise_speed, self.speed + random.uniform(20, 40))
                    self.start_speed_transition(return_target, "ease-in", 1.0)  # 빠르게 가속으로 복귀
        
        # 속도 이징(easing) 업데이트
        self.update_speed_with_easing()
        
        # 좌우 움직임 업데이트
        self.update_lane_position(road_left, road_right)
        
        # 감속 여부 확인 (브레이크등 관리용)
        self.check_deceleration()
    
    def update_speed_with_easing(self):
        """이징(easing) 방식으로 속도 업데이트"""
        if not self.is_speed_transitioning:
            return
            
        # 진행 시간 업데이트
        self.speed_transition_timer += 1/60  # 60fps 기준
        
        # 진행률 계산 (0~1)
        progress = min(1.0, self.speed_transition_timer / self.speed_transition_duration)
        
        # 이징 함수 적용
        if self.speed_transition_type == "linear":
            eased_progress = progress  # 선형 변화
        elif self.speed_transition_type == "ease-in":
            eased_progress = self.ease_in_cubic(progress)  # 시작 천천히
        elif self.speed_transition_type == "ease-out":
            eased_progress = self.ease_out_cubic(progress)  # 끝에 천천히
        else:  # "ease-in-out"
            eased_progress = self.ease_in_out_cubic(progress)  # 시작과 끝에 천천히
        
        # 현재 속도 계산
        target_diff = self.target_speed - self.speed_transition_start
        self.speed = self.speed_transition_start + target_diff * eased_progress
        
        # 속도 제한 적용 (80~160km/h 범위로 제한)
        self.speed = max(self.min_speed, min(self.max_speed, self.speed))
        
        # 이징 완료 확인
        if progress >= 1.0:
            self.is_speed_transitioning = False
            self.speed = self.target_speed
    
    def start_speed_transition(self, target_speed, transition_type="ease-in-out", duration=None):
        """속도 이징(easing) 전환 시작"""
        # 목표 속도를 80~160 범위로 제한
        self.target_speed = max(self.min_speed, min(self.max_speed, target_speed))
        self.speed_transition_start = self.speed
        self.speed_transition_type = transition_type
        
        # 전환 지속 시간 - 속도 차이에 따라 동적 조정 (지정된 값이 없을 경우)
        if duration is None:
            speed_diff = abs(self.target_speed - self.speed)
            speed_ratio = speed_diff / (self.max_speed - self.min_speed)  # 변경된 속도 범위 기준
            
            # 가속/감속에 따라 다른 지속 시간
            if self.target_speed > self.speed:  # 가속
                # 가속은 빠르게 (0.5~1.5초로 조정)
                self.speed_transition_duration = max(0.5, min(1.5, 0.5 + speed_ratio * 1.0))
            else:  # 감속
                # 감속은 더 빠르게 (0.5~2.0초)
                self.speed_transition_duration = max(0.5, min(2.0, 0.5 + speed_ratio * 1.5))
        else:
            self.speed_transition_duration = duration
        
        # 전환 시작
        self.speed_transition_timer = 0
        self.is_speed_transitioning = True
    
    def ease_in_cubic(self, t):
        """Cubic 이징 함수 (In) - 시작 천천히"""
        return t * t * t
    
    def ease_out_cubic(self, t):
        """Cubic 이징 함수 (Out) - 끝에 천천히"""
        return 1 - pow(1 - t, 3)
    
    def ease_in_out_cubic(self, t):
        """Cubic 이징 함수 (In/Out) - 시작과 끝에 천천히"""
        if t < 0.5:
            return 4 * t * t * t
        else:
            return 1 - pow(-2 * t + 2, 3) / 2

    def check_deceleration(self):
        """감속 여부 확인 및 브레이크등 관리"""
        # 이전 속도와 현재 속도 비교하여 감속 중인지 확인
        speed_diff = self.prev_speed - self.speed
        
        # 임계값 이상 감속 중이라면 감속 상태로 설정하고 브레이크등 켜기
        if speed_diff > self.deceleration_threshold:
            self.is_decelerating = True
            self.brake_lights_on = True
        else:
            self.is_decelerating = False
            
            # 브레이크/후효과 상태가 아니라면 브레이크등 끄기
            if not self.is_braking and not self.brake_afterglow:
                self.brake_lights_on = False

    def update_lane_position(self, road_left, road_right):
        """차선 내에서 좌우 움직임 업데이트"""
        road_center = (road_left + road_right) // 2
        
        # 차선 변경 타이머 업데이트
        self.lane_change_timer += 1/60
        
        # 새로운 목표 위치 설정
        if self.lane_change_timer >= self.lane_change_interval:
            self.lane_change_timer = 0
            self.lane_change_interval = random.uniform(1.0, 2.5)  # 더 자주 움직이도록 변경 (1.5-3 → 1.0-2.5)
            
            # 차선 내에서 랜덤한 x 위치 선택
            max_deviation = min(self.max_lane_deviation, (road_right - road_left) // 2 - self.width // 2 - 5)
            self.target_x = road_center + random.uniform(-max_deviation, max_deviation)
        
        # 부드럽게 목표 위치로 이동
        if abs(self.x - self.target_x) > self.move_speed:
            if self.x < self.target_x:
                self.x += self.move_speed
            else:
                self.x -= self.move_speed
        
        # 도로 경계 확인 및 수정
        half_width = self.width // 2
        if self.x - half_width < road_left + 5:
            self.x = road_left + half_width + 5
            self.target_x = self.x + random.uniform(15, 30)  # 경계에 닿으면 안쪽으로 방향 전환 (10-20 → 15-30)
        elif self.x + half_width > road_right - 5:
            self.x = road_right - half_width - 5
            self.target_x = self.x - random.uniform(15, 30)  # 경계에 닿으면 안쪽으로 방향 전환 (10-20 → 15-30)

    def apply_brake(self):
        """브레이크 적용"""
        # 100km/h 미만에서는 브레이크를 적용하지 않음
        if self.speed < 100:
            return
            
        self.is_braking = True
        self.brake_time = 0
        # 브레이크 단계를 1 또는 2로 설정 (70% 확률로 강한 브레이크) - 더 극적인 감속을 위해 강한 브레이크 확률 증가 (60% → 70%)
        self.brake_intensity = random.choices([1, 2], weights=[30, 70], k=1)[0]
        
        # 브레이크 강도에 따라 브레이크 지속 시간 차별화
        if self.brake_intensity == 1:  # 약한 브레이크는 짧게
            self.brake_duration = random.uniform(1.5, 2.0)  # 더 짧게 (1.5-2.5 → 1.5-2.0)
        else:  # 강한 브레이크는 길게
            self.brake_duration = random.uniform(2.5, 4.0)  # 더 길게 (2.0-3.5 → 2.5-4.0)
            
        self.brake_timer = 0
        
        # 브레이크 적용 시 목표 속도 감소 (이징을 통해 점진적으로 적용)
        brake_amount = 60 if self.brake_intensity == 1 else 130  # 브레이크 효과 차이
        target_brake_speed = max(self.min_speed, self.speed - brake_amount)
        
        # 브레이크 강도에 따라 적절한 지속 시간과 이징 유형 선택
        if self.brake_intensity == 1:
            self.start_speed_transition(target_brake_speed, "ease-out", 1.2)  # 약한 브레이크는 짧게
        else:
            self.start_speed_transition(target_brake_speed, "ease-out", 1.8)  # 강한 브레이크는 길게
        
        # 브레이크등 켜기
        self.brake_lights_on = True
    
    def release_brake(self):
        """브레이크 해제"""
        self.is_braking = False
        
        # 브레이크 해제 시 목표 속도 증가 - 브레이크 강도에 따라 가속 정도 차별화 (순항 속도 기준으로 조정)
        if self.brake_intensity == 1:  # 약한 브레이크 후 복귀
            # 현재 속도와 순항 속도 사이의 차이를 고려한 목표 설정
            if self.speed < self.cruise_speed:
                # 순항 속도보다 느릴 경우 순항 속도까지 가속
                target_speed = min(self.cruise_speed + 10, self.speed + random.uniform(20, 30))
            else:
                # 순항 속도보다 빠를 경우 현재 속도 유지 또는 약간 감속
                target_speed = max(self.cruise_speed, self.speed - random.uniform(5, 15))
                
            # 속도 제한 적용
            target_speed = max(self.min_speed, min(self.max_speed, target_speed))
                
            # 가속은 빠르게 (0.8초 내외)
            self.start_speed_transition(target_speed, "ease-in", 0.8)
        else:  # 강한 브레이크 후 강한 가속
            if self.speed < self.cruise_speed - 30:
                # 많이 감속된 경우 순항 속도까지 빠르게 복귀
                target_speed = min(self.cruise_speed + 20, self.speed + random.uniform(40, 60))
                self.start_speed_transition(target_speed, "ease-in", 1.2)  # 빠른 가속
            else:
                # 적당히 감속된 경우 순항 속도 근처로 복귀
                target_speed = min(self.max_speed, self.cruise_speed + random.uniform(-10, 20))
                self.start_speed_transition(target_speed, "ease-in-out", 1.5)
        
        # 감속 중이 아니라면 브레이크등 끄기
        if not self.is_decelerating:
            self.brake_lights_on = False
    
    def draw(self, screen):
        """앞 차량 그리기"""
        # 차체 그리기
        pygame.draw.rect(screen, self.color, 
                        (self.x - self.width // 2, self.y - self.height // 2, 
                        self.width, self.height))
        
        # 후미등 그리기
        self.draw_brake_lights(screen)
        
        # 헤드라이트 그리기
        # 왼쪽 헤드라이트
        light_width = max(5, int(15 * self.visual_size))
        light_height = max(3, int(10 * self.visual_size))
        pygame.draw.rect(screen, (255, 255, 200),
                        (self.x - self.width // 2 + max(5, int(5 * self.visual_size)), 
                        self.y - self.height // 2 + max(5, int(5 * self.visual_size)),
                        light_width, light_height))
        
        # 오른쪽 헤드라이트
        pygame.draw.rect(screen, (255, 255, 200),
                        (self.x + self.width // 2 - max(5, int(5 * self.visual_size)) - light_width, 
                        self.y - self.height // 2 + max(5, int(5 * self.visual_size)),
                        light_width, light_height))
    
    def draw_brake_lights(self, screen):
        """브레이크 등 그리기"""
        back_y = self.y + self.height // 2 - max(5, int(10 * self.visual_size))
        base_width = int(self.width * 0.9)  # 브레이크 등의 폭을 차량 폭의 90%로 설정
        
        # 브레이크 등 색상 설정 (브레이크 중이거나 감속 중일 때 밝게)
        if self.brake_lights_on:
            brake_color = (255, 0, 0)  # 밝은 빨간색
            
            # 브레이크 등 그리기 (하나의 긴 브레이크 등으로 변경)
            light_height = max(3, int(8 * self.visual_size))
            light_x = self.x - base_width // 2
            pygame.draw.rect(screen, brake_color,
                          (light_x, back_y,
                           base_width, light_height))
            
            # 브레이크 강도에 따른 추가 효과
            if self.is_braking and self.brake_intensity == 2:
                # 강한 브레이크일 때 더 강렬한 효과
                reflection_height = max(2, int(4 * self.visual_size))
                reflection_y = back_y + light_height + 1
                
                # 바닥 반사 효과
                pygame.draw.rect(screen, (255, 0, 0, 180),
                              (light_x, reflection_y,
                               base_width, reflection_height))
                
                # 브레이크 등 주변 발광 효과
                glow_size = max(5, int(12 * self.visual_size))
                for i in range(3):  # 레이어 추가
                    glow_alpha = 150 - i * 40  # 점점 투명해지는 효과
                    glow_color = (255, 0, 0, glow_alpha)
                    pygame.draw.rect(screen, glow_color,
                                  (light_x - i*2, back_y - i*2,
                                   base_width + i*4, light_height + i*4),
                                  1)  # 테두리만 그리기
        else:
            # 기본 후미등 그리기 (어두운 빨간색)
            light_height = max(2, int(6 * self.visual_size))
            light_x = self.x - base_width // 2
            pygame.draw.rect(screen, (150, 0, 0),
                          (light_x, back_y,
                           base_width, light_height)) 