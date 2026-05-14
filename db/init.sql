-- 企业职工宿舍入住管理系统 - PostgreSQL 16 初始化
SET client_encoding = 'UTF8';

CREATE TABLE dormitories (
  id SERIAL PRIMARY KEY,
  building_number VARCHAR(32) NOT NULL UNIQUE,
  gender VARCHAR(16) NOT NULL CHECK (gender IN ('male', 'female', 'mixed')),
  floors INT NOT NULL DEFAULT 1,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE rooms (
  id SERIAL PRIMARY KEY,
  dormitory_id INT NOT NULL REFERENCES dormitories(id) ON DELETE CASCADE,
  floor_number INT NOT NULL,
  room_number VARCHAR(32) NOT NULL,
  room_type VARCHAR(16) NOT NULL CHECK (room_type IN ('single', 'quad', 'six')),
  status VARCHAR(16) NOT NULL DEFAULT 'normal' CHECK (status IN ('normal', 'maintenance')),
  UNIQUE (dormitory_id, room_number)
);

CREATE INDEX ix_rooms_dormitory ON rooms (dormitory_id);

CREATE TABLE beds (
  id SERIAL PRIMARY KEY,
  room_id INT NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
  bed_code VARCHAR(64) NOT NULL,
  status VARCHAR(16) NOT NULL DEFAULT 'vacant' CHECK (status IN ('vacant', 'occupied', 'maintenance')),
  UNIQUE (room_id, bed_code)
);

CREATE INDEX ix_beds_room ON beds (room_id);

CREATE TABLE checkin_applications (
  id SERIAL PRIMARY KEY,
  applicant_name VARCHAR(128) NOT NULL,
  employee_no VARCHAR(64),
  reason TEXT,
  expected_date DATE,
  status VARCHAR(16) NOT NULL DEFAULT 'pending' CHECK (
    status IN ('pending', 'approved', 'rejected', 'cancelled')
  ),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE checkin_records (
  id SERIAL PRIMARY KEY,
  application_id INT REFERENCES checkin_applications (id),
  bed_id INT NOT NULL REFERENCES beds (id),
  employee_name VARCHAR(128) NOT NULL,
  employee_no VARCHAR(64),
  checkin_date DATE NOT NULL,
  deposit_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
  key_received BOOLEAN NOT NULL DEFAULT FALSE,
  status VARCHAR(16) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'checked_out')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX ux_checkin_bed_active ON checkin_records (bed_id)
WHERE
  status = 'active';

CREATE INDEX ix_checkin_employee ON checkin_records (employee_name);

CREATE TABLE fee_configs (
  id SERIAL PRIMARY KEY,
  room_type VARCHAR(16) NOT NULL UNIQUE,
  monthly_rate NUMERIC(12, 2) NOT NULL
);

CREATE TABLE fee_records (
  id SERIAL PRIMARY KEY,
  checkin_record_id INT NOT NULL REFERENCES checkin_records (id) ON DELETE CASCADE,
  billing_month DATE NOT NULL,
  amount_due NUMERIC(12, 2) NOT NULL,
  amount_paid NUMERIC(12, 2) NOT NULL DEFAULT 0,
  paid_at TIMESTAMPTZ,
  reminder_count INT NOT NULL DEFAULT 0,
  UNIQUE (checkin_record_id, billing_month)
);

CREATE INDEX ix_fee_records_arrears ON fee_records (billing_month)
WHERE
  amount_paid < amount_due;

CREATE TABLE swap_applications (
  id SERIAL PRIMARY KEY,
  checkin_record_id INT NOT NULL REFERENCES checkin_records (id),
  reason TEXT,
  expected_room_hint VARCHAR(128),
  status VARCHAR(16) NOT NULL DEFAULT 'pending' CHECK (
    status IN ('pending', 'approved', 'rejected')
  ),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE swap_histories (
  id SERIAL PRIMARY KEY,
  checkin_record_id INT NOT NULL REFERENCES checkin_records (id),
  from_bed_id INT NOT NULL,
  to_bed_id INT NOT NULL,
  reason TEXT,
  operated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE checkout_applications (
  id SERIAL PRIMARY KEY,
  checkin_record_id INT NOT NULL REFERENCES checkin_records (id),
  planned_date DATE NOT NULL,
  reason TEXT,
  status VARCHAR(16) NOT NULL DEFAULT 'pending' CHECK (
    status IN ('pending', 'approved', 'done', 'rejected')
  ),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE checkout_records (
  id SERIAL PRIMARY KEY,
  checkin_record_id INT NOT NULL UNIQUE REFERENCES checkin_records (id),
  checkout_date DATE NOT NULL,
  inspection_damage BOOLEAN NOT NULL DEFAULT FALSE,
  damage_notes TEXT,
  deposit_refund_amount NUMERIC(12, 2) NOT NULL DEFAULT 0,
  key_returned BOOLEAN NOT NULL DEFAULT FALSE,
  processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE repair_orders (
  id SERIAL PRIMARY KEY,
  checkin_record_id INT REFERENCES checkin_records (id),
  room_id INT NOT NULL REFERENCES rooms (id),
  category VARCHAR(32) NOT NULL CHECK (
    category IN ('water_electric', 'door_window', 'bed', 'aircon', 'daily', 'other')
  ),
  description TEXT NOT NULL,
  urgency VARCHAR(16) NOT NULL DEFAULT 'normal' CHECK (
    urgency IN ('low', 'normal', 'high', 'urgent')
  ),
  status VARCHAR(16) NOT NULL DEFAULT 'open' CHECK (
    status IN ('open', 'assigned', 'in_progress', 'done', 'closed')
  ),
  assignee VARCHAR(128),
  completed_at TIMESTAMPTZ,
  rating SMALLINT CHECK (
    rating IS NULL
    OR (rating BETWEEN 1 AND 5)
  ),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO
  fee_configs (room_type, monthly_rate)
VALUES
  ('single', 1200.00),
  ('quad', 400.00),
  ('six', 300.00);

DO $$
DECLARE
  dorm_rec RECORD;
  rm_rec RECORD;
  bed_row RECORD;
  r_chk RECORD;
  v_room_type TEXT;
  v_bcnt INT;
  bi INT;
  app_id INT;
  cid INT;
  names TEXT [] := ARRAY[
    '张伟', '李娜', '王强', '刘洋', '陈静', '杨军', '赵敏', '黄涛', '周杰', '吴芳',
    '徐明', '孙丽', '马军', '朱琳', '胡斌', '郭艳', '何勇', '高玲', '林峰', '罗敏',
    '郑浩', '梁雪', '谢军', '宋佳', '唐勇', '韩梅', '冯刚', '于丹', '董超', '萧红',
    '程亮', '曹颖', '邓伟', '彭丽', '曾强', '叶敏', '苏浩', '卢芳', '蒋军', '蔡琳',
    '魏强', '薛敏', '叶军', '阎丽', '余浩', '潘芳', '杜军', '戴敏', '夏浩', '钟芳'
  ];
  idx INT := 1;
BEGIN
  -- 10 栋宿舍楼
  FOR g IN 1..10 LOOP
    INSERT INTO
      dormitories (building_number, gender, floors)
    VALUES
      (
        g::TEXT || '号楼',
        CASE (g % 3)
          WHEN 0 THEN 'male'
          WHEN 1 THEN 'female'
          ELSE 'mixed'
        END,
        5
      );
  END LOOP;

  FOR dorm_rec IN
  SELECT *
  FROM dormitories
  ORDER BY id LOOP
      -- 每栋 20 间房，共 200
      FOR rnum IN 1..20 LOOP
        v_room_type :=
        CASE (rnum % 4)
          WHEN 0 THEN 'single'
          WHEN 1 THEN 'quad'
          WHEN 2 THEN 'six'
          ELSE 'quad'
        END;
        INSERT INTO
          rooms (
            dormitory_id,
            floor_number,
            room_number,
            room_type,
            status
          )
        VALUES
          (
            dorm_rec.id,
            ((rnum - 1) / 5) + 1,
            (
              ((((rnum - 1) / 5) + 1) * 100) + (((rnum - 1) % 5) + 1)
            )::TEXT,
            v_room_type,
            'normal'
          );
      END LOOP;
    END LOOP;

  -- 为每间房生成床位
  FOR rm_rec IN
  SELECT *
  FROM rooms LOOP
      v_bcnt :=
      CASE rm_rec.room_type
        WHEN 'single' THEN 1
        WHEN 'quad' THEN 4
        WHEN 'six' THEN 6
        ELSE 1
      END;
      FOR bi IN 1..v_bcnt LOOP
        INSERT INTO
          beds (room_id, bed_code, status)
        VALUES
          (
            rm_rec.id,
            rm_rec.room_number || '-' || bi::TEXT,
            'vacant'
          );
      END LOOP;
    END LOOP;

  -- 预置住户：使用前 72 张床
  FOR bed_row IN (
    SELECT
      bd.id AS bed_id
    FROM beds bd
      JOIN rooms rm ON bd.room_id = rm.id
    ORDER BY rm.dormitory_id, rm.room_number, bd.id
      LIMIT 72
  )
  LOOP
    IF idx > array_length(names, 1) THEN
      EXIT;
    END IF;
    INSERT INTO
      checkin_applications (
        applicant_name,
        employee_no,
        reason,
        expected_date,
        status
      )
    VALUES (
      names [idx],
      'E' || lpad(idx::TEXT, 4, '0'),
      '新员工入职安置',
      CURRENT_DATE - 30 + (idx % 7),
      'approved'
    )
    RETURNING
      id INTO app_id;

    INSERT INTO checkin_records (
      application_id,
      bed_id,
      employee_name,
      employee_no,
      checkin_date,
      deposit_amount,
      key_received,
      status
    )
    VALUES (
      app_id,
      bed_row.bed_id,
      names [idx],
      'E' || lpad(idx::TEXT, 4, '0'),
      CURRENT_DATE - 28 + (idx % 14),
      800.00,
      TRUE,
      'active'
    )
    RETURNING
      id INTO cid;

    UPDATE beds
    SET
      status = 'occupied'
    WHERE
      id = bed_row.bed_id;

    idx := idx + 1;
  END LOOP;

  -- 部分账单与欠缴（前 40 条在住记录）
  FOR r_chk IN (
    SELECT id AS cid
    FROM checkin_records
    WHERE status = 'active'
    ORDER BY id
    LIMIT 40
  ) LOOP
    INSERT INTO fee_records (
      checkin_record_id,
      billing_month,
      amount_due,
      amount_paid,
      paid_at,
      reminder_count
    )
    VALUES (
      r_chk.cid,
      date_trunc('month', CURRENT_DATE - INTERVAL '1 month')::date,
      400.00,
      400.00,
      NOW(),
      0
    );
    INSERT INTO fee_records (
      checkin_record_id,
      billing_month,
      amount_due,
      amount_paid,
      paid_at,
      reminder_count
    )
    VALUES (
      r_chk.cid,
      date_trunc('month', CURRENT_DATE)::date,
      400.00,
      250.00,
      NULL,
      1
    );
  END LOOP;

  -- 报修工单样例（关联已有房间与一条入住记录）
INSERT INTO
  repair_orders (
    checkin_record_id,
    room_id,
    category,
    description,
    urgency,
    status,
    assignee,
    completed_at,
    rating
  )
SELECT
  cr.id,
  rm.id,
  'water_electric',
  '卫生间水龙头滴水',
  'normal',
  'done',
  '维修组-王工',
  NOW() - INTERVAL '2 days',
  4
FROM checkin_records cr
  JOIN beds bd ON cr.bed_id = bd.id
  JOIN rooms rm ON bd.room_id = rm.id
WHERE
  cr.status = 'active'
LIMIT 5;

INSERT INTO
  repair_orders (
    checkin_record_id,
    room_id,
    category,
    description,
    urgency,
    status
  )
SELECT
  cr.id,
  rm.id,
  'aircon',
  '空调制冷效果差',
  'high',
  'open'
FROM checkin_records cr
  JOIN beds bd ON cr.bed_id = bd.id
  JOIN rooms rm ON bd.room_id = rm.id
WHERE
  cr.status = 'active'
OFFSET 5
LIMIT 5;

END;
$$;
