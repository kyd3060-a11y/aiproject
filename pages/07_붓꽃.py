
    # =================================
    # 6. 알고리즘별 예측 결과 비교
    # =================================

    st.divider()
    st.markdown("### 🏆 3가지 알고리즘 예측 결과 비교")

    # 알고리즘별 예측 결과 표 만들기
    comparison_df = pd.DataFrame({
        "알고리즘": list(results.keys()),
        "예측 품종": [
            species_korean.get(v, v)
            for v in results.values()
        ],
        "교차 검증 정확도": [
            f"{scores[k]:.2f}%"
            for k in results.keys()
        ]
    })

    st.dataframe(
        comparison_df,
        use_container_width=True,
        hide_index=True
    )

    # 품종별 투표 수 계산
    vote_counts = pd.Series(
        list(results.values())
    ).value_counts()

    vote_df = pd.DataFrame({
        "품종": [
            species_korean.get(v, v)
            for v in vote_counts.index
        ],
        "예측 횟수": vote_counts.values
    })

    st.markdown("### 📊 품종별 예측 횟수")

    st.bar_chart(
        vote_df,
        x="품종",
        y="예측 횟수",
        y_min=0,
        y_max=3
    )

    # 가장 많은 표를 받은 품종 확인
    max_votes = vote_counts.max()

    winners = vote_counts[
        vote_counts == max_votes
    ].index.tolist()

    st.markdown("### 🥇 최종 예측 비교")

    if len(winners) == 1:

        winner = winners[0]

        if max_votes == 3:
            st.success(
                f"🎉 세 알고리즘 모두 "
                f"{species_korean.get(winner, winner)}으로 "
                "동일하게 예측했습니다!"
            )

        else:
            st.success(
                f"🏆 다수결 예측 결과: "
                f"{species_korean.get(winner, winner)} "
                f"({max_votes}/3표)"
            )

    else:

        st.warning(
            "세 알고리즘의 예측 결과가 서로 달라 "
            "다수결로 하나의 품종을 결정할 수 없습니다."
        )

    # 알고리즘 간 예측 일치 여부
    unique_predictions = set(results.values())

    if len(unique_predictions) == 1:
        st.info("세 알고리즘의 예측 결과가 모두 일치합니다.")
    else:
        st.info(
            f"세 알고리즘 중 예측 품종이 "
            f"{len(unique_predictions)}종류로 나뉘었습니다."
        )
