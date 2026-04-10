import datetime
import logging

class PolarisUtility:

    @staticmethod
    def port_datetime(arg: str) -> datetime.datetime:
        """
        Convert a string like 'Apr 14, 02:00' to a datetime with the current year.
        Returns 1 JAN 1970 if arg is empty or invalid.
        """
        default_dt = datetime.datetime(1970, 1, 1)

        if arg is None:
            return default_dt

        value = str(arg).strip()
        if not value:
            return default_dt

        if value.lower() in {"-", "--", "n/a", "na", "none", "unknown"}:
            return default_dt

        try:
            # Use current year (timezone-aware UTC)
            this_year = datetime.datetime.now(datetime.timezone.utc).year

            normalized_values = [value]
            parts = value.rsplit(" ", 1)
            if len(parts) == 2 and parts[1].isalpha() and len(parts[1]) <= 5:
                # Inputs like "Apr 3, 21:30 UTC" imply current year.
                normalized_values.append(parts[0].strip())

            # Accept both port table dates ("Apr 14, 02:00") and vessel detail
            # dates ("Apr 6").
            candidates = []
            for normalized in normalized_values:
                candidates.extend(
                    [
                        (f"{normalized} {this_year}", "%b %d, %H:%M %Y"),
                        (f"{normalized} {this_year}", "%b %d %Y"),
                        (normalized, "%Y-%m-%d"),
                    ]
                )

            for candidate, fmt in candidates:
                try:
                    return datetime.datetime.strptime(candidate, fmt)
                except ValueError:
                    continue

            raise ValueError(f"unsupported date format: {value}")
        except Exception as e:
            logging.warning(f"Could not parse port datetime from '{arg}': {e}")
            return default_dt

# ;;; Local Variables: ***
# ;;; mode:python ***
# ;;; End: ***
