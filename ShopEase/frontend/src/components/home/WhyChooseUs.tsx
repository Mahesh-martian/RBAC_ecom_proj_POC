import PropTypes from "prop-types";
import serviceOne from "../../../public/images/icon-1.webp";
import serviceTwo from "../../../public/images/icon-2.webp";
import serviceThree from "../../../public/images/icon-3.webp";
import serviceFour from "../../../public/images/icon-4.webp";
import Image from "next/image";
import Heading from "../shared/CustomHeading";

// Define a type for the service object
interface Service {
  img: { src: string }; 
  title: string;
  desc: string;
}

// Component Props type for the Card component
interface CardProps {
  service: Service;
}

const WhyChooseUs: React.FC  = () => {
  const serviceData: Service[] = [
    {
      img: serviceOne,
      title: "BIG DISCOUNTS",
      desc: "Integer Euismod Blandit Nunc Sit Amet Sollicitudin. Fusce Quis Orci Viverra, Cursus Justo.",
    },
    {
      img: serviceTwo,
      title: "FAST SHIPPING",
      desc: "Integer Euismod Blandit Nunc Sit Amet Sollicitudin. Fusce Quis Orci Viverra, Cursus Justo.",
    },
    {
      img: serviceThree,
      title: "SECURE PAYMENTS",
      desc: "Integer Euismod Blandit Nunc Sit Amet Sollicitudin. Fusce Quis Orci Viverra, Cursus Justo.",
    },
    {
      img: serviceFour,
      title: "ORDER TRACKING",
      desc: "Integer Euismod Blandit Nunc Sit Amet Sollicitudin. Fusce Quis Orci Viverra, Cursus Justo.",
    },
  ];

  const Card: React.FC<CardProps> = ({ service }) => {
    const { img, title, desc } = service;
    return (
      <div className="flex flex-col gap-y-4 md:px-4">
        <Image
          src={img.src}
          alt={title}
          className="max-w-[80px] object-cover"
          width={80}
          height={80}
        />
        <h4 className="text-2xl font-medium">{title}</h4>
        <p className="text-base font-secondary opacity-75">{desc}</p>
      </div>
    );
  };

  return (
    <section className="py-20 md:py-36">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <h5 className="font-secondary text-lg capitalize">
            Best In Business
          </h5>
          <Heading
            text="WHY CHOOSE US"
            className="text-4xl lg:text-6xl text-center pb-20"
          />
        </div>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-x-8">
          {serviceData.map((service, i) => (
            <Card service={service} key={i} />
          ))}
        </div>
      </div>
    </section>
  );
};

export default WhyChooseUs;
