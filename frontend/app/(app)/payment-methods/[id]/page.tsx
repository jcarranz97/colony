"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Formik } from "formik";
import {
  Button,
  FieldError,
  Input,
  Label,
  ListBox,
  Select,
  Spinner,
  TextField,
} from "@heroui/react";
import { PaymentMethodSchema } from "@/helpers/schemas";
import {
  getPaymentMethods,
  editPaymentMethod,
} from "@/components/payment-methods/actions";
import type { PaymentMethod } from "@/helpers/types";

export default function EditPaymentMethodPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [method, setMethod] = useState<PaymentMethod | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getPaymentMethods().then((res) => {
      if (res.success) {
        setMethod(res.data.find((m) => m.id === id) ?? null);
      }
      setLoading(false);
    });
  }, [id]);

  if (loading) {
    return (
      <div className="flex justify-center py-16">
        <Spinner />
      </div>
    );
  }

  if (!method) {
    return (
      <div className="flex flex-col items-center gap-4 py-16">
        <p className="text-default-500">Payment method not found.</p>
        <Button variant="ghost" onPress={() => router.push("/payment-methods")}>
          Back
        </Button>
      </div>
    );
  }

  return (
    <div className="max-w-md flex flex-col gap-6">
      <div className="flex items-center gap-3">
        <Button
          size="sm"
          variant="ghost"
          onPress={() => router.push("/payment-methods")}
        >
          ← Back
        </Button>
        <h1 className="text-2xl font-bold">Edit Payment Method</h1>
      </div>

      <Formik
        initialValues={{
          name: method.name,
          method_type: method.method_type,
          default_currency: method.default_currency,
        }}
        validationSchema={PaymentMethodSchema}
        onSubmit={async (values, { setSubmitting }) => {
          setError(null);
          const result = await editPaymentMethod(method.id, {
            name: values.name,
          });
          if (result.success) {
            router.push("/payment-methods");
          } else {
            setError(result.error.message);
          }
          setSubmitting(false);
        }}
      >
        {({
          values,
          errors,
          touched,
          setFieldValue,
          handleSubmit,
          isSubmitting,
        }) => (
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <TextField
              isInvalid={!!errors.name && !!touched.name}
              value={values.name}
              onChange={(v) => setFieldValue("name", v)}
            >
              <Label>Name</Label>
              <Input />
              {touched.name && errors.name && (
                <FieldError>{errors.name}</FieldError>
              )}
            </TextField>

            <Select.Root
              selectedKey={values.method_type || null}
              onSelectionChange={(key) =>
                setFieldValue("method_type", String(key))
              }
              isInvalid={!!errors.method_type && !!touched.method_type}
              fullWidth
            >
              <Label>Type</Label>
              <Select.Trigger>
                <Select.Value>
                  {({ isPlaceholder, selectedText }: any) =>
                    isPlaceholder ? (
                      <span className="text-default-400">Select type...</span>
                    ) : (
                      selectedText
                    )
                  }
                </Select.Value>
                <Select.Indicator />
              </Select.Trigger>
              {touched.method_type && errors.method_type && (
                <p className="text-xs text-danger">{errors.method_type}</p>
              )}
              <Select.Popover>
                <ListBox>
                  <ListBox.Item id="debit" textValue="Debit">
                    Debit
                  </ListBox.Item>
                  <ListBox.Item id="credit" textValue="Credit">
                    Credit
                  </ListBox.Item>
                  <ListBox.Item id="cash" textValue="Cash">
                    Cash
                  </ListBox.Item>
                  <ListBox.Item id="transfer" textValue="Transfer">
                    Transfer
                  </ListBox.Item>
                </ListBox>
              </Select.Popover>
            </Select.Root>

            <Select.Root
              selectedKey={values.default_currency || null}
              onSelectionChange={(key) =>
                setFieldValue("default_currency", String(key))
              }
              isInvalid={
                !!errors.default_currency && !!touched.default_currency
              }
              fullWidth
            >
              <Label>Currency</Label>
              <Select.Trigger>
                <Select.Value>
                  {({ isPlaceholder, selectedText }: any) =>
                    isPlaceholder ? (
                      <span className="text-default-400">
                        Select currency...
                      </span>
                    ) : (
                      selectedText
                    )
                  }
                </Select.Value>
                <Select.Indicator />
              </Select.Trigger>
              {touched.default_currency && errors.default_currency && (
                <p className="text-xs text-danger">{errors.default_currency}</p>
              )}
              <Select.Popover>
                <ListBox>
                  <ListBox.Item id="USD" textValue="USD">
                    USD
                  </ListBox.Item>
                  <ListBox.Item id="MXN" textValue="MXN">
                    MXN
                  </ListBox.Item>
                </ListBox>
              </Select.Popover>
            </Select.Root>

            {error && <p className="text-sm text-danger">{error}</p>}

            <div className="flex gap-2">
              <Button
                variant="ghost"
                onPress={() => router.push("/payment-methods")}
              >
                Cancel
              </Button>
              <Button type="submit" variant="primary" isDisabled={isSubmitting}>
                {isSubmitting ? <Spinner size="sm" /> : "Save Changes"}
              </Button>
            </div>
          </form>
        )}
      </Formik>
    </div>
  );
}
