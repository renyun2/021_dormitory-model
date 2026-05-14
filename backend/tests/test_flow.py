from datetime import date


async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_dorm_room_beds_flow(client):
    d = await client.post(
        "/api/dormitories",
        json={"building_number": "测试楼-A", "gender": "mixed", "floors": 3},
    )
    assert d.status_code == 200
    did = d.json()["id"]
    rm = await client.post(
        "/api/rooms",
        json={
            "dormitory_id": did,
            "floor_number": 1,
            "room_number": "T101",
            "room_type": "quad",
            "status": "normal",
        },
    )
    assert rm.status_code == 200
    rid = rm.json()["id"]
    beds = (await client.get("/api/beds", params={"room_id": rid})).json()
    assert len(beds) == 4
    bid = beds[0]["id"]
    app = await client.post(
        "/api/checkin-applications",
        json={
            "applicant_name": "测试员工",
            "employee_no": "T001",
            "reason": "测试",
            "expected_date": str(date.today()),
        },
    )
    aid = app.json()["id"]
    patch = await client.patch(f"/api/checkin-applications/{aid}/status", json={"status": "approved"})
    assert patch.status_code == 200
    chk = await client.post(
        "/api/checkin-records/from-application",
        json={
            "application_id": aid,
            "bed_id": bid,
            "checkin_date": str(date.today()),
            "deposit_amount": "500",
            "key_received": True,
        },
    )
    assert chk.status_code == 200
    occ = await client.get(f"/api/dormitories/{did}/occupancy")
    assert occ.status_code == 200
    assert len(occ.json()) >= 1
    vacant = (
        await client.get("/api/beds", params={"status": "vacant"})
    ).json()
    assert len(vacant) >= 3


async def test_fee_generation_and_arrears(client):
    """最小费用：需要先有一条在住 + 住宿费配置。"""
    d = (
        await client.post(
            "/api/dormitories",
            json={"building_number": "费用测试楼", "gender": "male", "floors": 2},
        )
    ).json()
    did = d["id"]
    rm = (
        await client.post(
            "/api/rooms",
            json={
                "dormitory_id": did,
                "floor_number": 1,
                "room_number": "F101",
                "room_type": "single",
                "status": "normal",
            },
        )
    ).json()
    beds = (
        await client.get("/api/beds", params={"room_id": rm["id"]})
    ).json()
    bid = beds[0]["id"]
    app = (
        await client.post("/api/checkin-applications", json={"applicant_name": "租客", "reason": "", "employee_no": "F1"})
    ).json()
    await client.patch(f"/api/checkin-applications/{app['id']}/status", json={"status": "approved"})
    chk = (
        await client.post(
            "/api/checkin-records/from-application",
            json={
                "application_id": app["id"],
                "bed_id": bid,
                "checkin_date": str(date.today()),
                "deposit_amount": "600",
                "key_received": True,
            },
        )
    ).json()
    await client.put("/api/fee-configs/single", json={"monthly_rate": 900})
    g = await client.post("/api/fee-records/generate-month", json={"year": 2026, "month": 6})
    assert g.status_code == 200
    assert g.json()["created_rows"] >= 1
    fees = (await client.get("/api/fee-records", params={"checkin_record_id": chk["id"]})).json()
    fid = fees[0]["id"]
    p = await client.post(f"/api/fee-records/{fid}/payment", json={"amount": 100})
    assert p.status_code == 200
    arrears = (await client.get("/api/fee-records", params={"arrears_only": True})).json()
    assert len(arrears) >= 1
