"use client";
import { useFormikContext } from "formik";
import {
  FieldError,
  Input,
  Label,
  ListBox,
  Select,
  Switch,
  TextField,
} from "@heroui/react";

const DAY_NAMES = [
  "Sunday",
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
  "Saturday",
];

interface FormValues {
  recurrence_type: string;
  recurrence_config: Record<string, unknown>;
  [key: string]: unknown;
}

export function RecurrenceConfigBuilder() {
  const { values, errors, touched, setFieldValue } =
    useFormikContext<FormValues>();

  const recurrenceType = values.recurrence_type;
  const cfg = values.recurrence_config;
  const cfgErrors = (errors.recurrence_config as Record<string, string>) ?? {};
  const cfgTouched =
    (touched.recurrence_config as Record<string, boolean>) ?? {};

  switch (recurrenceType) {
    case "weekly":
      return (
        <Select.Root
          selectedKey={
            cfg.day_of_week !== undefined ? String(cfg.day_of_week) : null
          }
          onSelectionChange={(key) =>
            setFieldValue("recurrence_config", { day_of_week: Number(key) })
          }
          isInvalid={!!(cfgErrors.day_of_week && cfgTouched.day_of_week)}
          fullWidth
        >
          <Label>Day of Week</Label>
          <Select.Trigger>
            <Select.Value>
              {({ isPlaceholder, selectedText }: any) =>
                isPlaceholder ? (
                  <span className="text-default-400">Select day...</span>
                ) : (
                  selectedText
                )
              }
            </Select.Value>
            <Select.Indicator />
          </Select.Trigger>
          {cfgTouched.day_of_week && cfgErrors.day_of_week && (
            <p className="text-xs text-danger">{cfgErrors.day_of_week}</p>
          )}
          <Select.Popover>
            <ListBox>
              {DAY_NAMES.map((day, i) => (
                <ListBox.Item key={i} id={String(i)} textValue={day}>
                  {day}
                </ListBox.Item>
              ))}
            </ListBox>
          </Select.Popover>
        </Select.Root>
      );

    case "bi_weekly":
      return (
        <TextField
          isInvalid={!!(cfgErrors.interval_days && cfgTouched.interval_days)}
          value={
            cfg.interval_days !== undefined ? String(cfg.interval_days) : ""
          }
          onChange={(v) =>
            setFieldValue("recurrence_config", { interval_days: Number(v) })
          }
        >
          <Label>Interval Days</Label>
          <Input type="number" placeholder="14" />
          {cfgTouched.interval_days && cfgErrors.interval_days && (
            <FieldError>{cfgErrors.interval_days}</FieldError>
          )}
        </TextField>
      );

    case "monthly":
      return (
        <div className="flex flex-col gap-3">
          <TextField
            isInvalid={!!(cfgErrors.day_of_month && cfgTouched.day_of_month)}
            value={
              cfg.day_of_month !== undefined ? String(cfg.day_of_month) : ""
            }
            onChange={(v) =>
              setFieldValue("recurrence_config", {
                ...cfg,
                day_of_month: Number(v),
              })
            }
          >
            <Label>Day of Month</Label>
            <Input type="number" placeholder="1–31" />
            {cfgTouched.day_of_month && cfgErrors.day_of_month && (
              <FieldError>{cfgErrors.day_of_month}</FieldError>
            )}
          </TextField>
          <div className="flex items-center gap-3">
            <Switch
              isSelected={!!cfg.handle_month_end}
              onChange={(v: boolean) =>
                setFieldValue("recurrence_config", {
                  ...cfg,
                  handle_month_end: v,
                })
              }
              size="sm"
            >
              Handle month end
            </Switch>
          </div>
        </div>
      );

    case "custom":
      return (
        <div className="flex flex-col gap-3">
          <TextField
            isInvalid={!!(cfgErrors.interval && cfgTouched.interval)}
            value={cfg.interval !== undefined ? String(cfg.interval) : ""}
            onChange={(v) =>
              setFieldValue("recurrence_config", {
                ...cfg,
                interval: Number(v),
              })
            }
          >
            <Label>Every N</Label>
            <Input type="number" placeholder="e.g. 2" />
            {cfgTouched.interval && cfgErrors.interval && (
              <FieldError>{cfgErrors.interval}</FieldError>
            )}
          </TextField>
          <Select.Root
            selectedKey={(cfg.unit as string) || null}
            onSelectionChange={(key) =>
              setFieldValue("recurrence_config", { ...cfg, unit: String(key) })
            }
            isInvalid={!!(cfgErrors.unit && cfgTouched.unit)}
            fullWidth
          >
            <Label>Unit</Label>
            <Select.Trigger>
              <Select.Value>
                {({ isPlaceholder, selectedText }: any) =>
                  isPlaceholder ? (
                    <span className="text-default-400">Select unit...</span>
                  ) : (
                    selectedText
                  )
                }
              </Select.Value>
              <Select.Indicator />
            </Select.Trigger>
            {cfgTouched.unit && cfgErrors.unit && (
              <p className="text-xs text-danger">{cfgErrors.unit}</p>
            )}
            <Select.Popover>
              <ListBox>
                <ListBox.Item id="days" textValue="Days">
                  Days
                </ListBox.Item>
                <ListBox.Item id="weeks" textValue="Weeks">
                  Weeks
                </ListBox.Item>
                <ListBox.Item id="months" textValue="Months">
                  Months
                </ListBox.Item>
              </ListBox>
            </Select.Popover>
          </Select.Root>
        </div>
      );

    default:
      return null;
  }
}
