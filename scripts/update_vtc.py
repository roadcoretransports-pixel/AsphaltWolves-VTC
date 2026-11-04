
        "news":
            news["news"],

        "events":
            events["events"],

        "updatedAt":
            utc_now(),

        "diagnostics":
            diagnostics

    }


    # --------------------------------------------------------
    # Important safety check
    #
    # Never overwrite a known good live dataset with
    # completely unavailable data.
    # --------------------------------------------------------

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if status == "unavailable" and OUTPUT_FILE.exists():

        print(
            "TruckersMP is unavailable."
        )

        print(
            "Keeping existing data/vtc.json."
        )

        print(
            "No fake driver count will be written."
        )

        return 0


    # --------------------------------------------------------
    # Write JSON
    # --------------------------------------------------------

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            output,
            file,
            indent=2,
            ensure_ascii=False
        )

        file.write("\n")


    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print()
    print("==========================================")
    print(" Update complete")
    print("==========================================")

    print(
        f"Status: {status}"
    )

    print(
        f"Drivers: {members['driverCount']}"
    )

    print(
        f"News: {len(news['news'])}"
    )

    print(
        f"Events: {len(events['events'])}"
    )

    print(
        f"Output: {OUTPUT_FILE}"
    )

    # --------------------------------------------------------
    # Exit with error if TruckersMP is unavailable.
    #
    # This makes the GitHub Actions run clearly visible
    # as failed instead of silently pretending everything
    # worked.
    # --------------------------------------------------------

    if status == "unavailable":

        print()
        print(
            "WARNING: TruckersMP could not be reached."
        )

        print(
            "The workflow will be marked as failed."
        )

        return 1

    return 0


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    sys.exit(main())
